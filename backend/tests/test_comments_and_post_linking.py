import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.models import (
    Product, BusinessSettings, InstagramAccount,
    PostProductLink, ProcessedComment, Conversation, Customer, User
)
from app.services.instagram.webhook_parser import webhook_parser, ParsedCommentEvent
from app.services.ai.validator import factual_validator
from app.core.rate_limit import auth_rate_limiter
from app.workers.tasks import process_single_comment
from app.services.messaging.conversation_manager import ConversationManager


# ==================== 1. Webhook Parser Tests ====================

def test_parse_comment_webhook_payload():
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "1784140001",
                "time": 1700000000,
                "changes": [
                    {
                        "field": "comments",
                        "value": {
                            "id": "comment_998877",
                            "text": "What is the price of this Polki necklace in rupees?",
                            "from": {
                                "id": "user_follower_123",
                                "username": "ananya_jewels_fan"
                            },
                            "media": {
                                "id": "media_reel_5544"
                            },
                            "created_time": 1700000000
                        }
                    }
                ]
            }
        ]
    }

    events = webhook_parser.parse_comment_events(payload)
    assert len(events) == 1
    ev = events[0]
    assert ev.comment_id == "comment_998877"
    assert ev.media_id == "media_reel_5544"
    assert ev.from_user_id == "user_follower_123"
    assert ev.from_username == "ananya_jewels_fan"
    assert "price of this Polki" in ev.text
    assert ev.entry_id == "1784140001"


def test_parse_dm_with_shared_reel():
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "1784140001",
                "time": 1700000000,
                "messaging": [
                    {
                        "sender": {"id": "customer_456"},
                        "recipient": {"id": "1784140001"},
                        "timestamp": 1700000000000,
                        "message": {
                            "mid": "mid_reel_share_1",
                            "text": "Is this choker available?",
                            "attachments": [
                                {
                                    "type": "share",
                                    "payload": {
                                        "url": "https://www.instagram.com/reel/C8AbCdEfGhI/",
                                        "reel_id": "media_reel_5544"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    events = webhook_parser.parse_payload(payload)
    assert len(events) == 1
    ev = events[0]
    assert ev.shared_media_id == "media_reel_5544"
    assert "instagram.com/reel" in ev.shared_media_url


# ==================== 2. Validator Anti-Hallucination & Gap Tests ====================

def test_store_24k_rate_does_not_allow_24k_claim_on_18k_item():
    """
    CRITICAL FIX: Having gold_rate_24k set in settings must NOT allow
    claiming an 18K item is 24K gold.
    """
    settings = BusinessSettings(
        gold_rate_24k_per_10g=78000.0,
        gold_rate_22k_per_10g=72000.0,
        gold_rate_18k_per_10g=58000.0
    )
    product_18k = Product(
        sku="RNG-18K-01",
        name="18K Solitaire Ring",
        category="Rings",
        price=45000.0,
        gold_purity="18K",
        gross_weight=4.2
    )

    # Claiming 24K gold on an 18K product must FAIL validation
    deceptive_claim = "This ring is made of pure 24K gold for ₹45,000."
    is_valid, violations, final_text = factual_validator.validate_response(
        response_text=deceptive_claim,
        products=[product_18k],
        settings=settings,
        language="en"
    )

    assert is_valid is False
    assert any("24K" in v for v in violations)
    assert "specialist" in final_text.lower()


def test_weight_auditing_against_catalogue_specs():
    """
    CRITICAL FIX: Weight claims are audited against catalogue gross/net weights (+/- 0.5g tolerance).
    """
    product = Product(
        sku="CH-01",
        name="Diamond Choker",
        category="Necklaces",
        price=180000.0,
        gold_purity="18K",
        gross_weight=22.5
    )

    # Within tolerance: 22.8g (diff 0.3g <= 0.5g)
    valid_weight_claim = "The Diamond Choker is ₹180,000, 18K, with gross weight around 22.8g."
    is_valid, violations, _ = factual_validator.validate_response(
        response_text=valid_weight_claim,
        products=[product],
        language="en"
    )
    assert is_valid is True

    # Beyond tolerance: 15.0g (diff 7.5g > 0.5g)
    hallucinated_weight_claim = "The Diamond Choker is ₹180,000, 18K, with gross weight around 15g."
    is_valid, violations, final_text = factual_validator.validate_response(
        response_text=hallucinated_weight_claim,
        products=[product],
        language="en"
    )
    assert is_valid is False
    assert any("weight" in v.lower() for v in violations)
    assert "specialist" in final_text.lower()


def test_price_audited_when_zero_products_retrieved():
    """
    CRITICAL FIX: Prices are audited even when 0 products were retrieved.
    An unverified price quote must be blocked.
    """
    unverified_quote = "We can craft custom earrings starting at ₹8,500."
    is_valid, violations, final_text = factual_validator.validate_response(
        response_text=unverified_quote,
        products=[],  # Zero products retrieved
        settings=None,
        language="en"
    )

    assert is_valid is False
    assert any("₹8,500" in v for v in violations)
    assert "specialist" in final_text.lower()


# ==================== 3. Rate Limiter & Auth Security ====================

def test_auth_rate_limiter_blocks_excessive_attempts():
    ip = "192.168.1.100"
    # Reset limiter for this test
    auth_rate_limiter.requests.clear()

    # Allow up to 10 requests
    for i in range(10):
        assert auth_rate_limiter.is_allowed(ip, max_requests=10, window_seconds=60) is True

    # 11th request in the same minute must be blocked
    assert auth_rate_limiter.is_allowed(ip, max_requests=10, window_seconds=60) is False


# ==================== 4. Comment-to-DM Worker Logic ====================

def test_comment_processing_self_comment_skipped(db_session):
    account = InstagramAccount(
        user_id="user-1",
        ig_user_id="brand_ig_id",
        username="luxeaurajewels",
        token_encrypted="mock_token",
        is_connected=True
    )
    db_session.add(account)
    db_session.commit()

    conv_manager = ConversationManager(db_session)

    # Comment from the brand's own account
    comment_item = ParsedCommentEvent(
        comment_id="comment_self_1",
        media_id="media_123",
        from_user_id="brand_ig_id",
        from_username="luxeaurajewels",
        text="Check our website",
        timestamp=datetime.now(timezone.utc),
        entry_id="brand_ig_id"
    )

    process_single_comment(comment_item, db_session, conv_manager)

    # No ProcessedComment or outgoing DM should be recorded
    processed = db_session.query(ProcessedComment).filter_by(comment_id="comment_self_1").first()
    assert processed is None


def test_comment_processing_daily_cap_enforced(db_session):
    account = InstagramAccount(
        user_id="user-2",
        ig_user_id="brand_ig_id_2",
        username="brand_account_2",
        token_encrypted="mock_token",
        is_connected=True
    )
    db_session.add(account)
    db_session.commit()

    # Pre-populate 50 sent private replies today
    for i in range(50):
        db_session.add(
            ProcessedComment(
                instagram_account_id=account.id,
                comment_id=f"dummy_c_{i}",
                media_id="media_123",
                from_user_id=f"user_{i}",
                comment_text="Price?",
                intent="price",
                private_reply_sent=True,
                created_at=datetime.now(timezone.utc)
            )
        )
    db_session.commit()

    conv_manager = ConversationManager(db_session)
    comment_item = ParsedCommentEvent(
        comment_id="comment_overflow_51",
        media_id="media_123",
        from_user_id="follower_999",
        from_username="follower_999",
        text="Price please?",
        timestamp=datetime.now(timezone.utc),
        entry_id="brand_ig_id_2"
    )

    process_single_comment(comment_item, db_session, conv_manager)

    # Must be recorded as cap_exceeded and private_reply_sent == False
    processed = db_session.query(ProcessedComment).filter_by(comment_id="comment_overflow_51").first()
    assert processed is not None
    assert processed.intent == "cap_exceeded"
    assert processed.private_reply_sent is False


def test_comment_processing_respects_global_automation_switch(db_session):
    account = InstagramAccount(
        user_id="paused-owner", ig_user_id="paused-brand", username="paused_brand",
        token_encrypted="must_not_be_decrypted", is_connected=True,
    )
    account.settings = BusinessSettings(business_name="Paused shop", auto_reply_enabled=False)
    db_session.add(account)
    db_session.flush()
    db_session.add(PostProductLink(
        instagram_account_id=account.id, media_id="paused-media", product_ids=[],
        auto_dm_enabled=True, public_reply_enabled=True, is_active=True,
    ))
    db_session.commit()
    comment = ParsedCommentEvent(
        comment_id="paused-comment", media_id="paused-media", from_user_id="customer-paused",
        from_username="customer", text="Price please", timestamp=datetime.now(timezone.utc), entry_id="paused-brand",
    )
    with patch("app.workers.tasks.instagram_client.send_private_reply_to_comment", new_callable=AsyncMock) as send:
        process_single_comment(comment, db_session, ConversationManager(db_session))
        send.assert_not_called()
    processed = db_session.query(ProcessedComment).filter_by(comment_id="paused-comment").first()
    assert processed is not None
    assert processed.intent == "automation_paused"
    assert processed.private_reply_sent is False
