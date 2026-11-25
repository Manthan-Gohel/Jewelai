"""Loopback-only QA backend: disposable data, synthetic providers, no private .env."""
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
QA_DIR = Path(tempfile.mkdtemp(prefix="jewelai-buttons-"))
os.chdir(QA_DIR)
sys.path.insert(0, str(ROOT / "backend"))
from cryptography.fernet import Fernet
os.environ.update({
    "ENVIRONMENT": "development", "TESTING": "True", "DEBUG": "False",
    "DATABASE_URL": "sqlite:///" + (QA_DIR / "qa.db").as_posix(),
    "SECRET_KEY": "synthetic-local-qa-secret-not-for-deployment-2026",
    "ENCRYPTION_KEY": Fernet.generate_key().decode(),
    "REGISTRATION_INVITE_CODE": "local-buttons-invite", "ENABLE_OPEN_REGISTRATION": "False",
    "ENABLE_DIRECT_TOKEN_CONNECT": "False", "MOCK_INSTAGRAM_API": "True", "MOCK_AI_PROVIDER": "True",
    "INSTAGRAM_APP_ID": "synthetic-qa-app", "INSTAGRAM_APP_SECRET": "synthetic-qa-app-secret",
    "INSTAGRAM_WEBHOOK_VERIFY_TOKEN": "synthetic-local-webhook-token", "GEMINI_API_KEY": "",
    "INSTAGRAM_REDIRECT_URI": "http://127.0.0.1:3013/auth/instagram/callback",
    "CORS_ORIGINS": '["http://127.0.0.1:3013"]', "AUTH_RATE_LIMIT_PER_MINUTE": "1000",
})

from fastapi import Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import Base, engine, SessionLocal, get_db
from app.core.security import hash_password
from app.api.deps import get_current_instagram_account
from app.models.models import User, InstagramAccount, Customer, Conversation, Message, ProcessedComment
from app.services.instagram.oauth import instagram_oauth
from app.services.instagram.client import instagram_client

Base.metadata.create_all(engine)
with SessionLocal() as db:
    db.add(User(name="QA Operator", email="qa-operator@example.com", password_hash=hash_password("Local-qa-only-2026!"), role="owner"))
    db.add(User(name="QA Client", email="buttons-client@example.com", password_hash=hash_password("Buttons-qa-only-2026!"), role="staff"))
    db.commit()

# Keep real state creation/validation and all application endpoints. Only provider transport is local.
instagram_oauth.oauth_dialog_url = "/api/v1/qa/authorize"

@app.get("/api/v1/qa/authorize")
def authorize(state: str):
    return RedirectResponse("http://127.0.0.1:3013/auth/instagram/callback?code=synthetic-code&state=" + state)

async def recent_media(*args, **kwargs):
    return [{"id": "qa-post-1", "caption": "Synthetic QA ring post", "media_type": "VIDEO", "timestamp": "2026-11-25T10:00:00+0000"}]
instagram_client.get_recent_media = recent_media

@app.post("/api/v1/qa/seed")
def seed(account: InstagramAccount = Depends(get_current_instagram_account), db: Session = Depends(get_db)):
    existing = db.query(Conversation).filter_by(instagram_account_id=account.id).all()
    if existing:
        return {"conversation_ids": [item.id for item in existing]}
    now = datetime.now(timezone.utc)
    ids = []
    for i, (username, status, elapsed) in enumerate([("qa_recent", "active", 1), ("qa_waiting", "pending_human", 30)]):
        customer = Customer(instagram_account_id=account.id, instagram_user_id=f"qa-recipient-{i}", username=username, full_name=f"QA Customer {i}", preferred_language="en")
        db.add(customer)
        db.flush()
        conversation = Conversation(instagram_account_id=account.id, customer_id=customer.id, status=status, ai_enabled=status == "active", human_takeover=False, last_customer_message_at=now-timedelta(hours=elapsed), last_message_at=now-timedelta(minutes=i))
        db.add(conversation)
        db.flush()
        db.add(Message(conversation_id=conversation.id, meta_message_id=f"qa-message-{i}", sender_type="customer", message_type="text", content=f"QA customer enquiry {i}", delivery_status="received"))
        ids.append(conversation.id)
    db.add(ProcessedComment(instagram_account_id=account.id, comment_id="qa-comment-1", media_id="qa-post-1", from_user_id="qa-commenter", from_username="qa_commenter", comment_text="Price please?", intent="price_inquiry", private_reply_sent=False, public_reply_sent=False))
    db.commit()
    return {"conversation_ids": ids}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="warning")
