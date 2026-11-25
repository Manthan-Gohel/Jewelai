import json
import hmac
import hashlib
import time
from datetime import datetime, timezone
from app.core.config import settings
from app.models.models import Message, Conversation, Customer, InstagramAccount, WebhookEvent
from app.workers.tasks import process_webhook_event_logic


def test_end_to_end_incoming_message_to_ai_reply(client, db_session):
    account = db_session.query(InstagramAccount).first()
    test_mid = "mid.e2e_live_test_001"
    customer_igsid = "customer_ig_scoped_888"
    now_ms = int(time.time() * 1000)

    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": account.ig_user_id,
                "time": int(time.time()),
                "messaging": [
                    {
                        "sender": {"id": customer_igsid},
                        "recipient": {"id": account.ig_user_id},
                        "timestamp": now_ms,
                        "message": {
                            "mid": test_mid,
                            "text": "Hi, do you have gold earrings under ₹15,000?"
                        }
                    }
                ]
            }
        ]
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    signature = hmac.new(
        key=settings.INSTAGRAM_APP_SECRET.encode("utf-8"),
        msg=raw_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    # 1. Post to Webhook endpoint
    response = client.post(
        "/api/v1/webhooks/instagram",
        content=raw_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={signature}"
        }
    )
    assert response.status_code == 200

    # 2. Verify WebhookEvent stored
    event = db_session.query(WebhookEvent).order_by(WebhookEvent.received_at.desc()).first()
    assert event is not None
    assert event.signature_verified is True

    # 3. Execute Worker Pipeline
    processed = process_webhook_event_logic(event.id, db_session)
    assert processed is True

    # 4. Verify Customer, Conversation, and Messages created
    customer = db_session.query(Customer).filter(Customer.instagram_user_id == customer_igsid).first()
    assert customer is not None

    conv = db_session.query(Conversation).filter(Conversation.customer_id == customer.id).first()
    assert conv is not None

    messages = db_session.query(Message).filter(Message.conversation_id == conv.id).all()
    assert len(messages) >= 2  # 1 incoming from customer + 1 outgoing from AI
    
    incoming_msg = next((m for m in messages if m.sender_type == "customer"), None)
    ai_msg = next((m for m in messages if m.sender_type == "ai"), None)

    assert incoming_msg is not None
    assert incoming_msg.meta_message_id == test_mid
    assert ai_msg is not None
    assert len(ai_msg.content) > 0


def test_duplicate_webhook_event_prevention(client, db_session):
    account = db_session.query(InstagramAccount).first()
    duplicate_mid = "mid.dedup_test_999"
    customer_igsid = "customer_ig_scoped_999"

    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": account.ig_user_id,
                "messaging": [
                    {
                        "sender": {"id": customer_igsid},
                        "recipient": {"id": account.ig_user_id},
                        "timestamp": 1718000000,
                        "message": {
                            "mid": duplicate_mid,
                            "text": "Hello, is this shop open?"
                        }
                    }
                ]
            }
        ]
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    signature = hmac.new(
        key=settings.INSTAGRAM_APP_SECRET.encode("utf-8"),
        msg=raw_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    # Send 1st time
    res1 = client.post(
        "/api/v1/webhooks/instagram",
        content=raw_bytes,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": f"sha256={signature}"}
    )
    assert res1.status_code == 200

    # Process 1st event
    event1 = db_session.query(WebhookEvent).order_by(WebhookEvent.received_at.desc()).first()
    assert event1 is not None
    process_webhook_event_logic(event1.id, db_session)

    # Count messages after 1st processing
    customer = db_session.query(Customer).filter(Customer.instagram_user_id == customer_igsid).first()
    assert customer is not None
    conv = db_session.query(Conversation).filter(Conversation.customer_id == customer.id).first()
    assert conv is not None
    count_after_first = db_session.query(Message).filter(Message.conversation_id == conv.id).count()

    # Send 2nd duplicate event with identical mid
    res2 = client.post(
        "/api/v1/webhooks/instagram",
        content=raw_bytes,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": f"sha256={signature}"}
    )
    assert res2.status_code == 200

    event2 = db_session.query(WebhookEvent).order_by(WebhookEvent.received_at.desc()).first()
    assert event2 is not None
    process_webhook_event_logic(event2.id, db_session)

    # Count messages after 2nd duplicate attempt - must be unchanged because mid is duplicate
    count_after_second = db_session.query(Message).filter(Message.conversation_id == conv.id).count()
    assert count_after_second == count_after_first
