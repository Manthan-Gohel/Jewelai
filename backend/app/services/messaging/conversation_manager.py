from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session
import logging

from app.models.models import Customer, Conversation, Message, InstagramAccount, BusinessSettings, AutomationLog
from app.core.security import decrypt_token
from app.services.instagram.policy import policy_service
from app.services.instagram.client import instagram_client

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages customer threads, message deduplication, human takeover, and delivery tracking.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_customer(
        self,
        account_id: str,
        instagram_user_id: str,
        username: Optional[str] = None,
        name: Optional[str] = None
    ) -> Customer:
        customer = self.db.query(Customer).filter(
            Customer.instagram_account_id == account_id,
            Customer.instagram_user_id == instagram_user_id
        ).first()

        if not customer:
            customer = Customer(
                instagram_account_id=account_id,
                instagram_user_id=instagram_user_id,
                username=username,
                full_name=name,
                last_active_at=datetime.now(timezone.utc)
            )
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)
        else:
            if username and not customer.username:
                customer.username = username
            customer.last_active_at = datetime.now(timezone.utc)
            self.db.commit()

        return customer

    def get_or_create_conversation(self, customer: Customer) -> Conversation:
        conversation = self.db.query(Conversation).filter(
            Conversation.customer_id == customer.id,
            Conversation.instagram_account_id == customer.instagram_account_id
        ).first()

        if not conversation:
            conversation = Conversation(
                customer_id=customer.id,
                instagram_account_id=customer.instagram_account_id,
                status="active",
                ai_enabled=True,
                human_takeover=False,
                last_customer_message_at=datetime.now(timezone.utc),
                last_message_at=datetime.now(timezone.utc)
            )
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

        return conversation

    def is_message_duplicate(self, meta_message_id: Optional[str]) -> bool:
        """Prevent duplicate processing of webhook retries."""
        if not meta_message_id:
            return False
        existing = self.db.query(Message).filter(Message.meta_message_id == meta_message_id).first()
        return existing is not None

    def record_incoming_message(
        self,
        conversation: Conversation,
        meta_message_id: str,
        text: Optional[str],
        media_urls: Optional[List[str]] = None,
        is_echo: bool = False,
        timestamp: Optional[datetime] = None
    ) -> Message:
        now = datetime.now(timezone.utc)
        message_time = timestamp or now
        if message_time.tzinfo is None:
            message_time = message_time.replace(tzinfo=timezone.utc)
        
        # Check human escalation keyword
        if text and policy_service.check_escalation_keywords(text):
            logger.info(f"Escalation keyword matched in conversation {conversation.id}. Transferring to human.")
            conversation.human_takeover = True
            conversation.human_takeover_at = message_time
            conversation.status = "pending_human"

        if not is_echo:
            # Set to the official Meta message timestamp, NOT server arrival time,
            # so network delays and webhook retries do not artificially reopen the 24h window.
            conversation.last_customer_message_at = message_time
            conversation.unread_count = (conversation.unread_count or 0) + 1

        conversation.last_message_at = message_time
        
        msg = Message(
            conversation_id=conversation.id,
            meta_message_id=meta_message_id,
            sender_type="customer" if not is_echo else "human",
            message_type="image" if media_urls else "text",
            content=text,
            media_urls=media_urls or [],
            is_echo=is_echo,
            delivery_status="received",
            sent_at=message_time
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def record_outgoing_message(
        self,
        conversation: Conversation,
        content: str,
        sender_type: str = "ai",
        meta_message_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        delivery_status: str = "sent",
        error_message: Optional[str] = None
    ) -> Message:
        now = datetime.now(timezone.utc)
        conversation.last_message_at = now
        conversation.unread_count = 0  # reset on reply

        msg = Message(
            conversation_id=conversation.id,
            meta_message_id=meta_message_id,
            sender_type=sender_type,
            message_type="text",
            content=content,
            metadata_json=metadata or {},
            delivery_status=delivery_status,
            error_message=error_message,
            sent_at=now
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg
