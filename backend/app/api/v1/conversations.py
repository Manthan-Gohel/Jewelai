from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import decrypt_token
from app.models.models import Conversation, Message, Customer, InstagramAccount
from app.schemas.schemas import (
    ConversationResponse, ConversationDetailResponse,
    HumanReplyRequest, ConversationUpdateAI, MessageResponse
)
from app.api.deps import get_current_instagram_account
from app.services.messaging.conversation_manager import ConversationManager
from app.services.instagram.client import instagram_client

router = APIRouter()


@router.get("", response_model=List[ConversationResponse])
def list_conversations(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """List customer conversations with live status and latest message."""
    query = db.query(Conversation).filter(
        Conversation.instagram_account_id == account.id
    )

    if status_filter:
        query = query.filter(Conversation.status == status_filter)

    if search:
        query = query.join(Customer).filter(
            (Customer.username.ilike(f"%{search}%")) |
            (Customer.full_name.ilike(f"%{search}%"))
        )

    conversations = query.order_by(desc(Conversation.last_message_at)).offset(offset).limit(limit).all()

    result = []
    for conv in conversations:
        latest = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(desc(Message.created_at)).first()

        result.append(
            ConversationResponse(
                id=conv.id,
                customer=conv.customer,
                status=conv.status,
                ai_enabled=conv.ai_enabled,
                human_takeover=conv.human_takeover,
                last_customer_message_at=conv.last_customer_message_at,
                last_message_at=conv.last_message_at,
                unread_count=conv.unread_count or 0,
                latest_message=MessageResponse.model_validate(latest) if latest else None
            )
        )

    return result


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: str,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """Get full conversation detail and message history."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.instagram_account_id == account.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Mark as read
    conv.unread_count = 0
    db.commit()

    return conv


@router.post("/{conversation_id}/reply", response_model=MessageResponse)
async def send_human_reply(
    conversation_id: str,
    reply: HumanReplyRequest,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """
    Staff sends manual reply:
    1. Sends message through Meta Send API
    2. Automatically engages Human Takeover mode to pause AI
    3. Persists human message in thread
    """
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.instagram_account_id == account.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    customer = conv.customer
    access_token = decrypt_token(account.token_encrypted)

    # Send via Instagram Send API
    send_result = await instagram_client.send_text_message(
        recipient_id=customer.instagram_user_id,
        text=reply.content,
        access_token=access_token
    )

    out_mid = send_result.get("message_id")

    # Automatically activate human takeover
    conv.human_takeover = True
    conv.human_takeover_at = datetime.now(timezone.utc)
    conv.status = "pending_human"
    conv.unread_count = 0

    conv_manager = ConversationManager(db)
    msg = conv_manager.record_outgoing_message(
        conversation=conv,
        content=reply.content,
        sender_type="human",
        meta_message_id=out_mid
    )

    return msg


@router.patch("/{conversation_id}/ai", response_model=ConversationResponse)
def update_conversation_ai_state(
    conversation_id: str,
    update_data: ConversationUpdateAI,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """
    Enable/disable AI or toggle Human Takeover for this specific customer thread.
    Clicking 'Resume AI' resets human_takeover to False and sets ai_enabled to True.
    """
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.instagram_account_id == account.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if update_data.ai_enabled is not None:
        conv.ai_enabled = update_data.ai_enabled

    if update_data.human_takeover is not None:
        conv.human_takeover = update_data.human_takeover
        if not update_data.human_takeover:
            # Resumed AI
            conv.status = "active"
            conv.ai_enabled = True
        else:
            conv.status = "pending_human"
            conv.human_takeover_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(conv)

    latest = db.query(Message).filter(
        Message.conversation_id == conv.id
    ).order_by(desc(Message.created_at)).first()

    return ConversationResponse(
        id=conv.id,
        customer=conv.customer,
        status=conv.status,
        ai_enabled=conv.ai_enabled,
        human_takeover=conv.human_takeover,
        last_customer_message_at=conv.last_customer_message_at,
        last_message_at=conv.last_message_at,
        unread_count=conv.unread_count or 0,
        latest_message=MessageResponse.model_validate(latest) if latest else None
    )
