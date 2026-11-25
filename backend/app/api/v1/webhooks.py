import json
import logging
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Response, BackgroundTasks, HTTPException, status, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.security import verify_meta_webhook_signature
from app.models.models import WebhookEvent
from app.workers.tasks import process_incoming_webhook_event, process_webhook_event_logic

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/instagram")
async def verify_webhook(request: Request):
    """
    Official Meta Webhook verification handshake.
    Query parameters:
    - hub.mode: 'subscribe'
    - hub.verify_token: your configured verification token
    - hub.challenge: integer challenge string to echo back
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    logger.info(f"Received webhook verification handshake: mode={mode}, token_matches={token == settings.INSTAGRAM_WEBHOOK_VERIFY_TOKEN}")

    if mode == "subscribe" and token == settings.INSTAGRAM_WEBHOOK_VERIFY_TOKEN:
        logger.info(f"Webhook verification successful. Echoing challenge.")
        return PlainTextResponse(content=challenge or "", status_code=200)

    logger.warning("Webhook verification failed: token mismatch or invalid mode")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch"
    )


def run_background_worker_fallback(event_id: str):
    """Fallback processor if Celery worker is offline."""
    db = SessionLocal()
    try:
        process_webhook_event_logic(event_id, db)
    except Exception as e:
        logger.error(f"Fallback worker error for event {event_id}: {e}")
    finally:
        db.close()


@router.post("/instagram")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Ingest incoming Meta Webhook events.
    1. Verify HMAC SHA256 signature in X-Hub-Signature-256
    2. Persist raw payload to webhook_events
    3. Enqueue asynchronous background processing
    4. Return HTTP 200 OK immediately < 200ms
    """
    body_bytes = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256")

    # 1. Verify HMAC signature
    is_valid_signature = verify_meta_webhook_signature(
        payload_bytes=body_bytes,
        signature_header=signature_header
    )

    if not is_valid_signature:
        logger.error("Meta Webhook rejected: Invalid HMAC SHA256 signature")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid request signature"
        )

    # 2. Parse JSON payload
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        logger.error(f"Failed to parse webhook JSON payload: {e}")
        return Response(content="EVENT_RECEIVED", status_code=200)

    # 3. Persist Event to Database
    event = WebhookEvent(
        event_type=payload.get("object", "instagram"),
        payload_json=payload,
        signature_verified=True,
        processed=False,
        received_at=datetime.now(timezone.utc)
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    event_id = event.id

    # 4. Asynchronously Enqueue
    queued_via_celery = False
    try:
        process_incoming_webhook_event.delay(event_id)
        queued_via_celery = True
    except Exception as exc:
        logger.warning(f"Celery unavailable ({exc}), falling back to direct background task")

    if not queued_via_celery:
        background_tasks.add_task(run_background_worker_fallback, event_id)

    return Response(content="EVENT_RECEIVED", status_code=200)
