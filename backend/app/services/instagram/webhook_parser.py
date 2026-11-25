from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ParsedMessageEvent:
    def __init__(
        self,
        sender_id: str,
        recipient_id: str,
        timestamp: datetime,
        message_id: str,
        text: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        is_echo: bool = False,
        is_handoff: bool = False,
        handoff_type: Optional[str] = None,
        entry_id: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None
    ):
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.timestamp = timestamp
        self.message_id = message_id
        self.text = text or ""
        self.attachments = attachments or []
        self.is_echo = is_echo
        self.is_handoff = is_handoff
        self.handoff_type = handoff_type
        self.entry_id = entry_id
        self.raw_payload = raw_payload or {}

    @property
    def has_image(self) -> bool:
        return any(att.get("type") == "image" for att in self.attachments)

    @property
    def first_image_url(self) -> Optional[str]:
        for att in self.attachments:
            if att.get("type") == "image":
                return att.get("payload", {}).get("url")
        return None

    @property
    def shared_media_id(self) -> Optional[str]:
        """Extract media_id / reel_id if customer shared a reel or post in this DM."""
        for att in self.attachments:
            att_type = att.get("type", "")
            if att_type in ["share", "ig_reel", "story_share", "story_mention"]:
                payload = att.get("payload", {})
                if "media" in payload and isinstance(payload["media"], dict):
                    mid = payload["media"].get("id")
                    if mid:
                        return str(mid)
                if payload.get("reel_id"):
                    return str(payload["reel_id"])
                if payload.get("id"):
                    return str(payload["id"])
        return None

    @property
    def shared_media_url(self) -> Optional[str]:
        for att in self.attachments:
            if att.get("type") in ["share", "ig_reel", "story_share", "story_mention"]:
                return att.get("payload", {}).get("url")
        return None


class ParsedCommentEvent:
    """
    Represents an incoming comment on an Instagram post, reel, or video.
    Received via Meta Webhooks with entry[].changes[].field == "comments".
    """
    def __init__(
        self,
        comment_id: str,
        media_id: str,
        from_user_id: str,
        from_username: Optional[str],
        text: str,
        timestamp: datetime,
        parent_id: Optional[str] = None,
        entry_id: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None
    ):
        self.comment_id = comment_id
        self.media_id = media_id
        self.from_user_id = from_user_id
        self.from_username = from_username
        self.text = text or ""
        self.timestamp = timestamp
        self.parent_id = parent_id
        self.entry_id = entry_id
        self.raw_payload = raw_payload or {}



class InstagramWebhookParser:
    """
    Parses official Meta Instagram Webhook JSON payloads.
    Documentation: https://developers.facebook.com/docs/messenger-platform/reference/webhook-events
    """

    @staticmethod
    def parse_payload(payload: Dict[str, Any]) -> List[ParsedMessageEvent]:
        events: List[ParsedMessageEvent] = []
        
        # Verify root object type
        obj_type = payload.get("object")
        if obj_type not in ["instagram", "page"]:
            logger.warning(f"Unexpected webhook object type: {obj_type}")
            return events

        entries = payload.get("entry", [])
        for entry in entries:
            entry_id = str(entry.get("id")) if entry.get("id") else None
            # Both 'messaging' and 'standby' events should be processed
            messaging_items = entry.get("messaging", []) + entry.get("standby", [])
            for item in messaging_items:
                sender = item.get("sender", {}).get("id")
                recipient = item.get("recipient", {}).get("id")
                raw_time = item.get("timestamp")
                
                if raw_time:
                    try:
                        timestamp = datetime.fromtimestamp(raw_time / 1000.0, tz=timezone.utc)
                    except Exception:
                        timestamp = datetime.now(timezone.utc)
                else:
                    timestamp = datetime.now(timezone.utc)

                # 1. Standard incoming message or echo
                if "message" in item:
                    msg = item["message"]
                    mid = msg.get("mid")
                    text = msg.get("text")
                    is_echo = msg.get("is_echo", False)
                    attachments = msg.get("attachments", [])

                    events.append(
                        ParsedMessageEvent(
                            sender_id=sender,
                            recipient_id=recipient,
                            timestamp=timestamp,
                            message_id=mid,
                            text=text,
                            attachments=attachments,
                            is_echo=is_echo,
                            entry_id=entry_id,
                            raw_payload=item
                        )
                    )

                # 2. Thread Control / Handoff events
                elif "pass_thread_control" in item:
                    events.append(
                        ParsedMessageEvent(
                            sender_id=sender,
                            recipient_id=recipient,
                            timestamp=timestamp,
                            message_id=f"handoff_pass_{timestamp.timestamp()}",
                            is_handoff=True,
                            handoff_type="pass_thread_control",
                            entry_id=entry_id,
                            raw_payload=item
                        )
                    )
                elif "take_thread_control" in item:
                    events.append(
                        ParsedMessageEvent(
                            sender_id=sender,
                            recipient_id=recipient,
                            timestamp=timestamp,
                            message_id=f"handoff_take_{timestamp.timestamp()}",
                            is_handoff=True,
                            handoff_type="take_thread_control",
                            entry_id=entry_id,
                            raw_payload=item
                        )
                    )

        return events

    @staticmethod
    def parse_comment_events(payload: Dict[str, Any]) -> List[ParsedCommentEvent]:
        """
        Extract comment events from Meta webhook payload.
        Meta sends comments in entry[].changes[] when field == 'comments'.
        """
        events: List[ParsedCommentEvent] = []
        obj_type = payload.get("object")
        if obj_type not in ["instagram", "page"]:
            return events

        entries = payload.get("entry", [])
        for entry in entries:
            entry_id = str(entry.get("id")) if entry.get("id") else None
            changes = entry.get("changes", [])
            for ch in changes:
                field = ch.get("field")
                if field in ["comments", "live_comments"]:
                    val = ch.get("value", {})
                    cid = val.get("id")
                    if not cid:
                        continue
                    text = val.get("text", "")
                    from_info = val.get("from", {})
                    from_uid = str(from_info.get("id", ""))
                    from_uname = from_info.get("username")
                    media_dict = val.get("media", {})
                    media_id = str(media_dict.get("id", "")) if media_dict else ""
                    parent_id = str(val.get("parent_id")) if val.get("parent_id") else None
                    created_time = val.get("created_time")
                    if created_time:
                        try:
                            ts = datetime.fromtimestamp(float(created_time), tz=timezone.utc)
                        except Exception:
                            ts = datetime.now(timezone.utc)
                    else:
                        ts = datetime.now(timezone.utc)

                    events.append(
                        ParsedCommentEvent(
                            comment_id=str(cid),
                            media_id=media_id,
                            from_user_id=from_uid,
                            from_username=from_uname,
                            text=text,
                            timestamp=ts,
                            parent_id=parent_id,
                            entry_id=entry_id,
                            raw_payload=ch
                        )
                    )
        return events


webhook_parser = InstagramWebhookParser()
