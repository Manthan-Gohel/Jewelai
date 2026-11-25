from datetime import datetime, timedelta, timezone
from app.services.instagram.policy import policy_service


def test_24_hour_messaging_window_allowed():
    """Messages received within 24 hours are permitted."""
    recent_time = datetime.now(timezone.utc) - timedelta(hours=2)
    assert policy_service.is_within_messaging_window(recent_time) is True


def test_24_hour_messaging_window_expired():
    """Messages older than 24 hours must be blocked per Meta policy."""
    old_time = datetime.now(timezone.utc) - timedelta(hours=26)
    assert policy_service.is_within_messaging_window(old_time) is False


def test_human_takeover_blocks_ai_reply():
    """When staff engages human takeover, AI responses are immediately paused."""
    now = datetime.now(timezone.utc)
    
    # Human takeover active -> Must be blocked
    can_reply, reason = policy_service.can_ai_respond(
        global_auto_reply=True,
        conversation_ai_enabled=True,
        human_takeover_active=True,
        last_customer_message_at=now
    )
    assert can_reply is False
    assert reason == "HUMAN_TAKEOVER_ACTIVE"

    # AI disabled per thread -> Must be blocked
    can_reply, reason = policy_service.can_ai_respond(
        global_auto_reply=True,
        conversation_ai_enabled=False,
        human_takeover_active=False,
        last_customer_message_at=now
    )
    assert can_reply is False
    assert reason == "CONVERSATION_AI_DISABLED"

    # All conditions clear -> Allowed
    can_reply, reason = policy_service.can_ai_respond(
        global_auto_reply=True,
        conversation_ai_enabled=True,
        human_takeover_active=False,
        last_customer_message_at=now
    )
    assert can_reply is True
    assert reason == "ALLOWED"


def test_escalation_keywords_detection():
    """Keywords requesting human assistance or expressing complaints must be detected."""
    assert policy_service.check_escalation_keywords("I want to speak to a human manager") is True
    assert policy_service.check_escalation_keywords("Can I talk to human staff please?") is True
    assert policy_service.check_escalation_keywords("koi maanas saathe vaat karavi aapo") is True
    assert policy_service.check_escalation_keywords("Do you have 22k gold bangles?") is False
