import json
import hmac
import hashlib
from app.core.config import settings
from app.services.instagram.webhook_parser import webhook_parser


def test_meta_webhook_get_verification_success(client):
    """Test official Meta webhook verification GET handshake."""
    response = client.get(
        "/api/v1/webhooks/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.INSTAGRAM_WEBHOOK_VERIFY_TOKEN,
            "hub.challenge": "11582012"
        }
    )
    assert response.status_code == 200
    assert response.text == "11582012"


def test_meta_webhook_get_verification_invalid_token(client):
    """Test webhook verification rejected on token mismatch."""
    response = client.get(
        "/api/v1/webhooks/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token_hacker",
            "hub.challenge": "11582012"
        }
    )
    assert response.status_code == 403


def test_meta_webhook_post_signature_validation(client):
    """Test incoming webhook POST requires valid Meta signature."""
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "17841400009999999",
                "time": 1718000000,
                "messaging": [
                    {
                        "sender": {"id": "customer_igsid_456"},
                        "recipient": {"id": "17841400009999999"},
                        "timestamp": 1718000000,
                        "message": {
                            "mid": "mid.test_webhook_001",
                            "text": "Do you have gold earrings under 15000?"
                        }
                    }
                ]
            }
        ]
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    
    # Compute HMAC
    signature = hmac.new(
        key=settings.INSTAGRAM_APP_SECRET.encode("utf-8"),
        msg=raw_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/v1/webhooks/instagram",
        content=raw_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={signature}"
        }
    )
    assert response.status_code == 200
    assert "EVENT_RECEIVED" in response.text


def test_webhook_parser_image_and_handoff():
    """Verify parsing of image attachments and handoff events."""
    payload_with_image = {
        "object": "instagram",
        "entry": [
            {
                "id": "17841400009999999",
                "messaging": [
                    {
                        "sender": {"id": "cust_1"},
                        "recipient": {"id": "17841400009999999"},
                        "timestamp": 1718000000,
                        "message": {
                            "mid": "mid.img_001",
                            "attachments": [
                                {
                                    "type": "image",
                                    "payload": {"url": "https://example.com/ring_reference.jpg"}
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    events = webhook_parser.parse_payload(payload_with_image)
    assert len(events) == 1
    assert events[0].has_image is True
    assert events[0].first_image_url == "https://example.com/ring_reference.jpg"
