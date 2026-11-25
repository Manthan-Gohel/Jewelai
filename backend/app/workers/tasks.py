import asyncio
from datetime import datetime, timezone, timedelta
import logging
import uuid
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import decrypt_token
from app.models.models import (
    WebhookEvent, InstagramAccount, Conversation,
    AutomationLog, BusinessSettings, Message,
    PostProductLink, ProcessedComment, Product
)
from app.services.instagram.webhook_parser import webhook_parser
from app.services.instagram.policy import policy_service
from app.services.instagram.client import instagram_client
from app.services.messaging.conversation_manager import ConversationManager
from app.services.ai.orchestrator import AIOrchestrator
from app.services.ai.gemini_provider import AIProviderError

logger = logging.getLogger(__name__)


def run_coro_sync(coro):
    """Safely run an async coroutine from sync context (Celery worker or FastAPI background task)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


def process_single_comment(comment_item, db: Session, conv_manager: ConversationManager):
    """
    Process an incoming comment on an Instagram post or reel:
    1. Resolve Instagram Business Account
    2. Skip brand's own comments
    3. Deduplicate comment ID
    4. Enforce daily auto-DM cap (settings.COMMENT_AUTO_DM_DAILY_CAP)
    5. Match post/reel media_id against PostProductLink
    6. Classify customer intent (price, details, interested, general)
    7. Send official Meta Private Reply DM (POST /v22.0/me/messages with recipient: {comment_id})
    8. Optionally post public reply ('Sent you a DM 📩')
    9. Record conversation context (source_media_id, context_product_ids)
    """
    # 1. Resolve Instagram Account
    account = None
    if getattr(comment_item, "entry_id", None):
        account = db.query(InstagramAccount).filter(
            InstagramAccount.ig_user_id == comment_item.entry_id,
            InstagramAccount.is_connected == True
        ).first()

    if not account and (settings.ENVIRONMENT != "production" and settings.DEBUG):
        account = db.query(InstagramAccount).filter(InstagramAccount.is_connected == True).first()

    if not account:
        logger.warning(f"No connected InstagramAccount matches entry_id {comment_item.entry_id} for comment {comment_item.comment_id}")
        return

    # 2. Skip comments made by brand's own account
    if comment_item.from_user_id == account.ig_user_id:
        logger.info(f"Skipping self-comment {comment_item.comment_id} from brand account {account.ig_user_id}")
        return

    # 3. Deduplication check: check if comment_id was already processed
    existing_comment = db.query(ProcessedComment).filter(
        ProcessedComment.comment_id == comment_item.comment_id
    ).first()
    if existing_comment:
        logger.info(f"Comment {comment_item.comment_id} already processed. Skipping.")
        return

    # 4. Check Daily Auto-DM Cap
    since_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    sent_today = db.query(ProcessedComment).filter(
        ProcessedComment.instagram_account_id == account.id,
        ProcessedComment.private_reply_sent == True,
        ProcessedComment.created_at >= since_24h
    ).count()

    if sent_today >= settings.COMMENT_AUTO_DM_DAILY_CAP:
        logger.warning(
            f"Daily auto-DM cap ({settings.COMMENT_AUTO_DM_DAILY_CAP}) reached for account {account.id}. "
            f"Skipping private reply for comment {comment_item.comment_id}"
        )
        record = ProcessedComment(
            instagram_account_id=account.id,
            comment_id=comment_item.comment_id,
            media_id=comment_item.media_id,
            from_user_id=comment_item.from_user_id,
            from_username=comment_item.from_username,
            comment_text=comment_item.text,
            intent="cap_exceeded",
            private_reply_sent=False,
            public_reply_sent=False,
            error_message=f"Daily auto-DM cap of {settings.COMMENT_AUTO_DM_DAILY_CAP} exceeded"
        )
        db.add(record)
        db.commit()
        return

    # 5. Find active PostProductLink for media_id
    link = db.query(PostProductLink).filter(
        PostProductLink.instagram_account_id == account.id,
        PostProductLink.media_id == comment_item.media_id,
        PostProductLink.is_active == True
    ).first()

    if not link or not link.auto_dm_enabled:
        logger.info(f"No active auto-DM link for media {comment_item.media_id}. Comment {comment_item.comment_id} recorded without reply.")
        record = ProcessedComment(
            instagram_account_id=account.id,
            comment_id=comment_item.comment_id,
            media_id=comment_item.media_id,
            from_user_id=comment_item.from_user_id,
            from_username=comment_item.from_username,
            comment_text=comment_item.text,
            intent="unlinked",
            private_reply_sent=False,
            public_reply_sent=False
        )
        db.add(record)
        db.commit()
        return

    # 6. Intent classification
    text_lower = comment_item.text.lower()
    if any(k in text_lower for k in ["price", "cost", "rate", "bhav", "kitna", "kevatla", "how much", "rs", "inr", "daam"]):
        intent = "price"
    elif any(k in text_lower for k in ["weight", "gram", "purity", "karat", "carat", "gold", "diamond", "size", "spec"]):
        intent = "details"
    elif any(k in text_lower for k in ["dm", "buy", "interested", "want", "order", "purchase", "details", "info"]):
        intent = "interested"
    else:
        intent = "inquiry"

    # 7. Fetch linked products
    linked_prods = []
    if link.product_ids:
        linked_prods = db.query(Product).filter(
            Product.id.in_(link.product_ids),
            Product.instagram_account_id == account.id
        ).all()

    # 8. Synthesize Private Reply DM
    biz_settings = db.query(BusinessSettings).filter(
        BusinessSettings.instagram_account_id == account.id
    ).first()
    if not biz_settings or not biz_settings.auto_reply_enabled:
        db.add(ProcessedComment(
            instagram_account_id=account.id,
            comment_id=comment_item.comment_id,
            media_id=comment_item.media_id,
            from_user_id=comment_item.from_user_id,
            from_username=comment_item.from_username,
            comment_text=comment_item.text,
            intent="automation_paused",
            private_reply_sent=False,
            public_reply_sent=False,
        ))
        db.commit()
        return
    store_name = biz_settings.business_name if biz_settings else "our showroom"

    if link.custom_reply_template:
        reply_text = link.custom_reply_template
        if linked_prods:
            p0 = linked_prods[0]
            reply_text = reply_text.replace("{product_name}", p0.name)
            reply_text = reply_text.replace("{price}", f"₹{p0.price:,.0f}")
            reply_text = reply_text.replace("{purity}", p0.gold_purity or "Pure Gold")
            reply_text = reply_text.replace("{sku}", p0.sku)
    else:
        greeting = f"Namaste from {store_name}! ✨ Thank you for your interest in our reel."
        if linked_prods:
            prod_lines = []
            for p in linked_prods:
                p_desc = f"• {p.name}: ₹{p.price:,.0f} ({p.gold_purity or 'Pure Gold'}"
                if p.gross_weight:
                    p_desc += f", {p.gross_weight}g"
                p_desc += ")"
                prod_lines.append(p_desc)
            details_str = "\n".join(prod_lines)
            reply_text = (
                f"{greeting}\n\nHere are the verified details for the featured piece:\n{details_str}\n\n"
                "Would you like more photos, custom sizing, or to place an order? "
                "Reply directly to this DM and our jewellery consultant will assist you! 💍"
            )
        else:
            reply_text = (
                f"{greeting}\n\nWe received your enquiry regarding this design. "
                "Reply directly to this DM with any questions, and our jewellery consultant will be delighted to help! 💍"
            )

    # 9. Send Private Reply via Instagram Send API
    access_token = decrypt_token(account.token_encrypted)
    private_reply_sent = False
    error_msg = None

    try:
        send_res = run_coro_sync(
            instagram_client.send_private_reply_to_comment(
                comment_id=comment_item.comment_id,
                text=reply_text,
                access_token=access_token
            )
        )
        private_reply_sent = True
        logger.info(f"Private reply sent for comment {comment_item.comment_id}, mid={send_res.get('message_id')}")
    except Exception as err:
        logger.error(f"Failed to send private reply for comment {comment_item.comment_id}: {err}")
        error_msg = str(err)

    # 10. Send Public Reply if enabled
    public_reply_sent = False
    if private_reply_sent and link.public_reply_enabled and link.public_reply_text:
        try:
            pub_res = run_coro_sync(
                instagram_client.post_public_reply_to_comment(
                    comment_id=comment_item.comment_id,
                    message=link.public_reply_text,
                    access_token=access_token
                )
            )
            if pub_res.get("status") != "failed":
                public_reply_sent = True
        except Exception as pub_err:
            logger.warning(f"Failed to post public reply for comment {comment_item.comment_id}: {pub_err}")

    # 11. Record ProcessedComment
    processed = ProcessedComment(
        instagram_account_id=account.id,
        comment_id=comment_item.comment_id,
        media_id=comment_item.media_id,
        from_user_id=comment_item.from_user_id,
        from_username=comment_item.from_username,
        comment_text=comment_item.text,
        intent=intent,
        private_reply_sent=private_reply_sent,
        public_reply_sent=public_reply_sent,
        error_message=error_msg
    )
    db.add(processed)

    # 12. Create Customer & Conversation context
    if private_reply_sent:
        customer = conv_manager.get_or_create_customer(
            account_id=account.id,
            instagram_user_id=comment_item.from_user_id,
            username=comment_item.from_username
        )
        conversation = conv_manager.get_or_create_conversation(customer)
        conversation.source_media_id = link.media_id
        conversation.context_product_ids = link.product_ids
        conversation.last_customer_message_at = comment_item.timestamp

        # Record outgoing message in thread
        conv_manager.record_outgoing_message(
            conversation=conversation,
            content=reply_text,
            sender_type="ai",
            meta_message_id=f"priv_reply_{comment_item.comment_id}",
            metadata={
                "type": "private_reply_to_comment",
                "comment_id": comment_item.comment_id,
                "media_id": comment_item.media_id,
                "intent": intent,
                "linked_products": link.product_ids
            }
        )

    db.commit()


def process_webhook_event_logic(event_id: str, db: Session) -> bool:
    """
    Core pipeline logic for processing incoming Meta Instagram Webhook events.
    1. Parse and extract events (messaging, handoff, standby, comments)
    2. Process comment events (Video Post/Reel -> Comments -> Auto DM)
    3. Check idempotency and deduplicate message IDs
    4. Resolve Instagram Business Account with account-level data isolation
    5. Handle shared reel/post context in DMs
    6. Enforce Meta 24-hour messaging window & human takeover policy gates
    7. Execute AI Orchestrator with contextual product prioritization
    8. Deliver verified response via Meta Instagram Send API (text + carousel/image)
    9. Escalate to human staff on any AI provider failure (no mock responses in production)
    """
    event = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
    if not event or event.processed:
        return True

    payload = event.payload_json
    conv_manager = ConversationManager(db)

    # Phase A: Process Comments Webhook Events (Reel / Video Post -> Auto DM)
    parsed_comments = webhook_parser.parse_comment_events(payload)
    if parsed_comments:
        for comment_item in parsed_comments:
            try:
                process_single_comment(comment_item, db, conv_manager)
            except Exception as c_err:
                logger.error(f"Error processing comment {comment_item.comment_id}: {c_err}", exc_info=True)

    # Phase B: Process Direct Messaging Events
    parsed_events = webhook_parser.parse_payload(payload)

    if not parsed_events and not parsed_comments:
        event.processed = True
        event.processed_at = datetime.now(timezone.utc)
        db.commit()
        return True

    if not parsed_events:
        event.processed = True
        event.processed_at = datetime.now(timezone.utc)
        db.commit()
        return True

    for item in parsed_events:
        # 1. Thread Handoff event handling
        if item.is_handoff:
            logger.info(f"Received handoff event {item.handoff_type} for sender {item.sender_id}")
            continue

        # 2. Skip message echoes
        if item.is_echo:
            logger.info(f"Received message echo mid={item.message_id}. Skipping AI reply.")
            continue

        # 3. Message Deduplication check (Idempotent webhook handling)
        if conv_manager.is_message_duplicate(item.message_id):
            logger.info(f"Duplicate message mid={item.message_id} ignored.")
            continue

        # 4. Resolve Instagram Account with strict account isolation
        account = None
        if item.recipient_id:
            account = db.query(InstagramAccount).filter(
                InstagramAccount.ig_user_id == item.recipient_id,
                InstagramAccount.is_connected == True
            ).first()

        if not account and getattr(item, "entry_id", None):
            account = db.query(InstagramAccount).filter(
                InstagramAccount.ig_user_id == item.entry_id,
                InstagramAccount.is_connected == True
            ).first()

        # In dev/test only, fallback to first connected account if recipient_id not mapped
        if not account and (settings.ENVIRONMENT != "production" and settings.DEBUG):
            account = db.query(InstagramAccount).filter(InstagramAccount.is_connected == True).first()

        if not account:
            logger.warning(f"No connected InstagramAccount matches recipient {item.recipient_id}. Webhook ignored.")
            continue

        # 5. Customer & Conversation Resolution
        customer = conv_manager.get_or_create_customer(
            account_id=account.id,
            instagram_user_id=item.sender_id
        )
        conversation = conv_manager.get_or_create_conversation(customer)

        # Check if customer shared a reel or post in this DM
        if item.shared_media_id:
            link = db.query(PostProductLink).filter(
                PostProductLink.instagram_account_id == account.id,
                PostProductLink.media_id == item.shared_media_id,
                PostProductLink.is_active == True
            ).first()
            if link:
                logger.info(f"Customer shared linked reel {item.shared_media_id} with products {link.product_ids}")
                conversation.source_media_id = item.shared_media_id
                conversation.context_product_ids = link.product_ids
                db.commit()

        # 6. Record Customer Message in DB
        media_urls = [item.first_image_url] if item.first_image_url else []
        incoming_msg = conv_manager.record_incoming_message(
            conversation=conversation,
            meta_message_id=item.message_id,
            text=item.text,
            media_urls=media_urls,
            is_echo=False,
            timestamp=item.timestamp
        )

        # 7. Check Policy & Conversation Ownership
        biz_settings = db.query(BusinessSettings).filter(
            BusinessSettings.instagram_account_id == account.id
        ).first()
        global_auto_reply = biz_settings.auto_reply_enabled if biz_settings else True

        can_reply, reason = policy_service.can_ai_respond(
            global_auto_reply=global_auto_reply,
            conversation_ai_enabled=conversation.ai_enabled,
            human_takeover_active=conversation.human_takeover,
            last_customer_message_at=conversation.last_customer_message_at
        )

        if not can_reply:
            logger.info(f"AI response skipped for conversation {conversation.id}: {reason}")
            log = AutomationLog(
                conversation_id=conversation.id,
                action="skipped_reply",
                error_detail=f"Policy gate: {reason}",
                validation_passed=False
            )
            db.add(log)
            db.commit()
            continue

        # 8. Run AI Orchestrator Pipeline
        orchestrator = AIOrchestrator(db)
        
        # Load recent context
        recent_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).limit(6).all()
        
        context_history = [
            {"sender": m.sender_type, "content": m.content or ""}
            for m in reversed(recent_messages)
        ]

        active_context_prods = conversation.context_product_ids or []

        try:
            ai_result = run_coro_sync(
                orchestrator.process_message(
                    account_id=account.id,
                    message_text=item.text,
                    image_url=item.first_image_url,
                    conversation_history=context_history,
                    context_product_ids=active_context_prods
                )
            )
            reply_text = ai_result["reply_text"]
            matched_products = ai_result.get("products", [])
        except (AIProviderError, Exception) as ai_err:
            logger.error(f"AI processing failed for conversation {conversation.id}: {ai_err}")
            # Escalate immediately to human staff
            conversation.human_takeover = True
            conversation.human_takeover_at = datetime.now(timezone.utc)
            conversation.status = "pending_human"

            store_name = biz_settings.business_name if biz_settings else "our showroom"
            fallback_text = (
                f"Thank you for reaching out to {store_name}! ✨ "
                "Our jewellery specialist has been notified and will assist you shortly with verified details."
            )

            # Record failure in automation logs
            log = AutomationLog(
                conversation_id=conversation.id,
                action="ai_failure_escalated",
                error_detail=f"AI Provider error: {str(ai_err)}",
                validation_passed=False
            )
            db.add(log)
            db.commit()

            # Safely send store transfer notification
            access_token = decrypt_token(account.token_encrypted)
            if access_token:
                try:
                    send_res = run_coro_sync(
                        instagram_client.send_text_message(
                            recipient_id=customer.instagram_user_id,
                            text=fallback_text,
                            access_token=access_token
                        )
                    )
                    conv_manager.record_outgoing_message(
                        conversation=conversation,
                        content=fallback_text,
                        sender_type="ai",
                        meta_message_id=send_res.get("message_id")
                    )
                except Exception as send_err:
                    logger.error(f"Failed to send fallback message: {send_err}")
            continue

        # 9. Re-check human takeover before sending (double-check race condition)
        db.refresh(conversation)
        if conversation.human_takeover:
            logger.info(f"Human took over conversation {conversation.id} during AI synthesis. Aborting send.")
            continue

        # 10. Send Response via Meta Send API
        access_token = decrypt_token(account.token_encrypted)
        try:
            send_result = run_coro_sync(
                instagram_client.send_text_message(
                    recipient_id=customer.instagram_user_id,
                    text=reply_text,
                    access_token=access_token
                )
            )
        except Exception as send_err:
            logger.error(f"Meta Send API failed to deliver message: {send_err}")
            # Record failed outgoing message with real Meta error
            conv_manager.record_outgoing_message(
                conversation=conversation,
                content=reply_text,
                sender_type="ai",
                delivery_status="failed",
                error_message=str(send_err),
                metadata={
                    "intent": ai_result.get("intent"),
                    "language": ai_result.get("language"),
                    "latency_ms": ai_result.get("latency_ms"),
                    "matched_sku": [p.sku for p in matched_products]
                }
            )
            log = AutomationLog(
                conversation_id=conversation.id,
                action="send_failed",
                intent_detected=ai_result.get("intent"),
                language_detected=ai_result.get("language"),
                retrieved_products_count=len(matched_products),
                ai_response_text=reply_text,
                error_detail=f"Meta Send API error: {str(send_err)}",
                validation_passed=ai_result.get("fact_validation_passed", True),
                latency_ms=ai_result.get("latency_ms", 0)
            )
            db.add(log)
            db.commit()
            continue

        # Deliver jewellery visual cards or photos if matching products have images
        products_with_images = [p for p in matched_products if getattr(p, "images", None)]
        if len(products_with_images) > 1:
            try:
                carousel_elements = instagram_client.build_product_generic_elements(products_with_images)
                run_coro_sync(
                    instagram_client.send_product_cards(
                        recipient_id=customer.instagram_user_id,
                        elements=carousel_elements,
                        access_token=access_token
                    )
                )
            except Exception as e:
                logger.warning(f"Could not send product carousel: {e}")
        elif len(products_with_images) == 1:
            primary_img = products_with_images[0].images[0].image_url
            try:
                run_coro_sync(
                    instagram_client.send_image_message(
                        recipient_id=customer.instagram_user_id,
                        image_url=primary_img,
                        access_token=access_token
                    )
                )
            except Exception as e:
                logger.warning(f"Could not send product image: {e}")

        # 11. Record Outgoing Message & Automation Log
        out_mid = send_result.get("message_id")
        if out_mid and db.query(Message).filter(Message.meta_message_id == out_mid).first():
            out_mid = f"{out_mid}_{uuid.uuid4().hex[:6]}"

        conv_manager.record_outgoing_message(
            conversation=conversation,
            content=reply_text,
            sender_type="ai",
            meta_message_id=out_mid,
            metadata={
                "intent": ai_result.get("intent"),
                "language": ai_result.get("language"),
                "latency_ms": ai_result.get("latency_ms"),
                "matched_sku": [p.sku for p in matched_products]
            }
        )

        log = AutomationLog(
            conversation_id=conversation.id,
            action="ai_reply_sent",
            intent_detected=ai_result.get("intent"),
            language_detected=ai_result.get("language"),
            retrieved_products_count=len(matched_products),
            ai_response_text=reply_text,
            validation_passed=ai_result.get("fact_validation_passed", True),
            latency_ms=ai_result.get("latency_ms", 0)
        )
        db.add(log)
        db.commit()

    event.processed = True
    event.processed_at = datetime.now(timezone.utc)
    db.commit()
    return True


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5, name="app.workers.tasks.process_incoming_webhook_event")
def process_incoming_webhook_event(self, event_id: str):
    """Celery task entry point with automatic retry on transient failures."""
    db = SessionLocal()
    try:
        process_webhook_event_logic(event_id, db)
    except Exception as exc:
        logger.error(f"Task failed for event {event_id}: {exc}")
        db.rollback()
        raise self.retry(exc=exc, countdown=5 * (2 ** self.request.retries))
    finally:
        db.close()
