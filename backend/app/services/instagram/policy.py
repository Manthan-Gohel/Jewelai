import re
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional, List
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class MessagingPolicyService:
    """
    Enforces Meta Platform Policies:
    - 24-hour standard messaging window
    - Conversation ownership / Human takeover enforcement
    - Escalation trigger detection
    """

    @staticmethod
    def is_within_messaging_window(
        last_customer_message_at: Optional[datetime],
        window_hours: int = settings.MESSAGING_WINDOW_HOURS
    ) -> bool:
        """
        Meta Official Policy: Businesses have 24 hours to respond to a customer's message.
        Responses outside this window violate Meta policy unless using a supported message tag.
        """
        if not last_customer_message_at:
            return False

        # Ensure datetime has timezone info
        if last_customer_message_at.tzinfo is None:
            last_customer_message_at = last_customer_message_at.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        elapsed = now - last_customer_message_at
        is_allowed = elapsed <= timedelta(hours=window_hours)
        
        if not is_allowed:
            logger.warning(
                f"Meta 24-hour window expired. Elapsed: {elapsed.total_seconds() / 3600:.1f}h > {window_hours}h"
            )
        return is_allowed

    @staticmethod
    def can_ai_respond(
        global_auto_reply: bool,
        conversation_ai_enabled: bool,
        human_takeover_active: bool,
        last_customer_message_at: Optional[datetime]
    ) -> Tuple[bool, str]:
        """
        Check all policy gates before allowing AI to generate and deliver a reply.
        Returns: (can_reply: bool, reason_code: str)
        """
        if not global_auto_reply:
            return False, "GLOBAL_AUTO_REPLY_DISABLED"

        if not conversation_ai_enabled:
            return False, "CONVERSATION_AI_DISABLED"

        if human_takeover_active:
            return False, "HUMAN_TAKEOVER_ACTIVE"

        if not MessagingPolicyService.is_within_messaging_window(last_customer_message_at):
            return False, "OUTSIDE_24H_MESSAGING_WINDOW"

        return True, "ALLOWED"

    @staticmethod
    def check_escalation_keywords(text: str, keywords: Optional[List[str]] = None) -> bool:
        """
        Check if customer text requests human staff, complaint handling, or unapproved negotiation.
        Uses regex word boundaries so words like 'management', 'damage', 'reagent' do NOT cause false takeovers.
        """
        if not text:
            return False
            
        default_patterns = [
            r"\btalk to (?:a )?human\b", r"\bspeak to (?:a )?human\b", r"\breal person\b",
            r"\bhuman agent\b", r"\bagent\b", r"\bmanager\b", r"\bcomplaint\b",
            r"\brefund\b", r"\bscam\b", r"\bcheat\b", r"\bdiscount please\b",
            r"\bbargain\b", r"\bcall me\b", r"\bphone number\b",
            r"\bmanas saathe vaat\b", r"\bmaanas\b", r"\bkoi chhe\b", r"\bcall karo\b"
        ]
        patterns = keywords or default_patterns
        lowered = text.lower()
        for p in patterns:
            # If pattern already has regex symbols or word boundary, use re.search; else match whole word
            regex = p if ("\\" in p or "(" in p) else rf"\b{re.escape(p)}\b"
            if re.search(regex, lowered, re.IGNORECASE):
                return True
        return False


policy_service = MessagingPolicyService()
