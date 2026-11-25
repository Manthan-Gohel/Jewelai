from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.models.models import (
    Message, Conversation, Product,
    InstagramAccount, AutomationLog
)
from app.schemas.schemas import DashboardOverviewMetrics
from app.api.deps import get_current_instagram_account

router = APIRouter()


@router.get("/overview", response_model=DashboardOverviewMetrics)
def get_dashboard_overview(
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    since_yesterday = now - timedelta(hours=24)

    total_msgs = db.query(Message).join(Conversation).filter(
        Conversation.instagram_account_id == account.id,
        Message.created_at >= since_yesterday
    ).count()

    ai_replies = db.query(Message).join(Conversation).filter(
        Conversation.instagram_account_id == account.id,
        Message.sender_type == "ai",
        Message.created_at >= since_yesterday
    ).count()

    pending_human = db.query(Conversation).filter(
        Conversation.instagram_account_id == account.id,
        Conversation.human_takeover == True
    ).count()

    active_convs = db.query(Conversation).filter(
        Conversation.instagram_account_id == account.id,
        Conversation.status.in_(["active", "pending_human"])
    ).count()

    products_count = db.query(Product).filter(
        Product.instagram_account_id == account.id,
        Product.status == "active"
    ).count()

    # Calculate success rate from automation logs
    total_logs = db.query(AutomationLog).join(Conversation).filter(
        Conversation.instagram_account_id == account.id,
        AutomationLog.created_at >= since_yesterday
    ).count()

    passed_logs = db.query(AutomationLog).join(Conversation).filter(
        Conversation.instagram_account_id == account.id,
        AutomationLog.validation_passed == True,
        AutomationLog.created_at >= since_yesterday
    ).count()

    success_rate = round((passed_logs / total_logs * 100), 1) if total_logs > 0 else 0
    average_latency_ms = db.query(func.avg(AutomationLog.latency_ms)).join(Conversation).filter(
        Conversation.instagram_account_id == account.id,
        AutomationLog.created_at >= since_yesterday,
        AutomationLog.latency_ms > 0,
    ).scalar()

    return DashboardOverviewMetrics(
        total_messages_today=total_msgs,
        ai_replies_today=ai_replies,
        pending_human_count=pending_human,
        ai_success_rate=success_rate,
        average_response_time_seconds=round(average_latency_ms / 1000, 2) if average_latency_ms else 0,
        active_conversations_count=active_convs,
        total_products_count=products_count,
        connected_account_username=account.username if account.is_connected else None,
        is_instagram_connected=account.is_connected
    )


@router.get("/logs")
def get_activity_logs(
    limit: int = 50,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    logs = db.query(AutomationLog).join(Conversation).filter(
        Conversation.instagram_account_id == account.id
    ).order_by(desc(AutomationLog.created_at)).limit(limit).all()

    return [
        {
            "id": l.id,
            "conversation_id": l.conversation_id,
            "action": l.action,
            "intent": l.intent_detected,
            "language": l.language_detected,
            "retrieved_products_count": l.retrieved_products_count,
            "ai_response": l.ai_response_text,
            "validation_passed": l.validation_passed,
            "error_detail": l.error_detail,
            "latency_ms": l.latency_ms,
            "created_at": l.created_at
        }
        for l in logs
    ]
