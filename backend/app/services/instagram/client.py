import httpx
import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class InstagramClient:
    """
    Official Meta Instagram Messaging Send API client (Graph API v22.0).
    Handles communication with official Meta endpoints for:
    - Text direct messages
    - Image attachments
    - Product carousel cards (generic templates)
    - User profile lookups
    """

    def __init__(self, api_version: str = settings.META_API_VERSION):
        self.api_version = api_version
        self.base_url = f"{settings.META_GRAPH_URL}/{api_version}"

    async def send_text_message(
        self,
        recipient_id: str,
        text: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Send a plaintext message to an Instagram user via Meta Send API.
        Endpoint: POST /{api_version}/me/messages
        """
        if settings.MOCK_INSTAGRAM_API or settings.ENVIRONMENT == "test":
            if not access_token or access_token.startswith("test_") or access_token.startswith("mock_"):
                logger.info(f"[TEST/MOCK] Sending text to {recipient_id}: {text[:60]}...")
                return {
                    "recipient_id": recipient_id,
                    "message_id": f"test_mid_{abs(hash(text))}",
                    "status": "sent"
                }

        if not access_token:
            raise ValueError("An active Instagram access token is required to send messages.")

        url = f"{self.base_url}/me/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Successfully sent text message to {recipient_id}, mid={data.get('message_id')}")
                return data
            except httpx.HTTPStatusError as e:
                logger.error(f"Meta Send API HTTP error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"Instagram Send API error ({e.response.status_code}): {e.response.text}")
            except Exception as e:
                logger.error(f"Failed to send Instagram message: {str(e)}")
                raise

    async def send_image_message(
        self,
        recipient_id: str,
        image_url: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Send a jewellery product photograph to an Instagram user.
        Endpoint: POST /{api_version}/me/messages
        """
        if settings.MOCK_INSTAGRAM_API or settings.ENVIRONMENT == "test":
            if not access_token or access_token.startswith("test_") or access_token.startswith("mock_"):
                logger.info(f"[TEST/MOCK] Sending image to {recipient_id}: {image_url}")
                return {
                    "recipient_id": recipient_id,
                    "message_id": f"test_mid_img_{abs(hash(image_url))}",
                    "status": "sent"
                }

        if not access_token:
            raise ValueError("An active Instagram access token is required to send image attachments.")

        url = f"{self.base_url}/me/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {
                        "url": image_url,
                        "is_reusable": True
                    }
                }
            }
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Meta Send Image API HTTP error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"Instagram Send Image API error: {e.response.text}")
            except Exception as e:
                logger.error(f"Failed to send Instagram image: {str(e)}")
                raise

    async def send_product_cards(
        self,
        recipient_id: str,
        elements: List[Dict[str, Any]],
        access_token: str
    ) -> Dict[str, Any]:
        """
        Send a generic template carousel showing jewellery items with photos, prices, and links.
        """
        if settings.MOCK_INSTAGRAM_API or settings.ENVIRONMENT == "test":
            if not access_token or access_token.startswith("test_") or access_token.startswith("mock_"):
                logger.info(f"[TEST/MOCK] Sending {len(elements)} product cards to {recipient_id}")
                return {
                    "recipient_id": recipient_id,
                    "message_id": f"test_mid_carousel_{len(elements)}",
                    "status": "sent"
                }

        if not access_token:
            raise ValueError("An active Instagram access token is required.")

        url = f"{self.base_url}/me/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "generic",
                        "elements": elements
                    }
                }
            }
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to send Instagram generic template: {str(e)}")
                raise

    async def get_user_profile(
        self,
        instagram_scoped_id: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Fetch public profile info for an Instagram scoped user.
        Fields: id, name, username, profile_pic
        """
        if settings.MOCK_INSTAGRAM_API or settings.ENVIRONMENT == "test":
            return {
                "id": instagram_scoped_id,
                "name": "Valued Customer",
                "username": f"customer_{instagram_scoped_id[-4:]}",
                "profile_pic": ""
            }

        url = f"{self.base_url}/{instagram_scoped_id}"
        params = {
            "fields": "id,name,username,profile_pic",
            "access_token": access_token
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                return {"id": instagram_scoped_id, "username": None, "name": None}
            except Exception as e:
                logger.warning(f"Could not fetch user profile for {instagram_scoped_id}: {e}")
                return {"id": instagram_scoped_id, "username": None, "name": None}

    async def get_recent_media(
        self,
        access_token: str,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent posts and reels published by the connected Instagram Business account.
        Endpoint: GET /{api_version}/me/media
        Fields: id, caption, media_type, media_url, permalink, thumbnail_url, timestamp
        """
        if settings.MOCK_INSTAGRAM_API or settings.ENVIRONMENT == "test":
            if not access_token or access_token.startswith("test_") or access_token.startswith("mock_"):
                logger.info("[TEST/MOCK] Returning simulated Instagram media items.")
                return [
                    {
                        "id": "18012345678901234",
                        "caption": "Royal Bridal Polki Choker with untreated emerald droplets ✨ #weddingjewels #polki",
                        "media_type": "VIDEO",
                        "permalink": "https://www.instagram.com/reel/C8AbCdEfGhI/",
                        "thumbnail_url": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f",
                        "timestamp": "2026-11-20T10:00:00+0000"
                    },
                    {
                        "id": "18098765432109876",
                        "caption": "Solitaire 18K Yellow Gold Diamond Ring — IGI certified, flawless sparkle 💍",
                        "media_type": "VIDEO",
                        "permalink": "https://www.instagram.com/reel/C8JkLmNoPqR/",
                        "thumbnail_url": "https://images.unsplash.com/photo-1605100804763-247f67b3557e",
                        "timestamp": "2026-11-22T14:30:00+0000"
                    }
                ]

        if not access_token:
            raise ValueError("An active Instagram access token is required to fetch media.")

        url = f"{self.base_url}/me/media"
        params = {
            "fields": "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp",
            "limit": limit,
            "access_token": access_token
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
            except httpx.HTTPStatusError as e:
                logger.error(f"Meta GET /me/media error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"Failed to fetch Instagram media ({e.response.status_code}): {e.response.text}")
            except Exception as e:
                logger.error(f"Failed to fetch Instagram media: {str(e)}")
                raise

    async def send_private_reply_to_comment(
        self,
        comment_id: str,
        text: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Send an official Meta Private Reply to a user's comment on a post/reel.
        Endpoint: POST /{api_version}/me/messages
        Payload: {"recipient": {"comment_id": comment_id}, "message": {"text": text}}
        
        Official Meta Constraints:
        - Must be sent within 7 days of the comment.
        - Exactly ONE private reply allowed per comment.
        - Requires 'instagram_business_manage_comments' permission.
        """
        if settings.MOCK_INSTAGRAM_API or settings.ENVIRONMENT == "test":
            if not access_token or access_token.startswith("test_") or access_token.startswith("mock_"):
                logger.info(f"[TEST/MOCK] Sending private reply to comment {comment_id}: {text[:60]}...")
                return {
                    "recipient_id": f"user_from_comment_{comment_id}",
                    "message_id": f"test_priv_mid_{abs(hash(comment_id))}",
                    "status": "sent"
                }

        if not access_token:
            raise ValueError("An active Instagram access token is required.")

        url = f"{self.base_url}/me/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "recipient": {"comment_id": comment_id},
            "message": {"text": text}
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Successfully sent private reply to comment {comment_id}, mid={data.get('message_id')}")
                return data
            except httpx.HTTPStatusError as e:
                logger.error(f"Meta Private Reply error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"Private Reply API error ({e.response.status_code}): {e.response.text}")
            except Exception as e:
                logger.error(f"Failed to send private reply to comment {comment_id}: {str(e)}")
                raise

    async def post_public_reply_to_comment(
        self,
        comment_id: str,
        message: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Post a public comment reply beneath the customer's comment (e.g. 'Sent you a DM 📩').
        Endpoint: POST /{api_version}/{comment_id}/replies
        Payload: {"message": message}
        """
        if settings.MOCK_INSTAGRAM_API or settings.ENVIRONMENT == "test":
            if not access_token or access_token.startswith("test_") or access_token.startswith("mock_"):
                logger.info(f"[TEST/MOCK] Public reply to comment {comment_id}: {message}")
                return {
                    "id": f"test_reply_{abs(hash(message))}",
                    "status": "published"
                }

        if not access_token:
            raise ValueError("An active Instagram access token is required.")

        url = f"{self.base_url}/{comment_id}/replies"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "message": message
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.warning(f"Meta Public Reply error: {e.response.status_code} - {e.response.text}")
                return {"error": e.response.text, "status": "failed"}
            except Exception as e:
                logger.warning(f"Failed to post public reply: {str(e)}")
                return {"error": str(e), "status": "failed"}

    def build_product_generic_elements(
        self,
        products: List[Any],
        currency_symbol: str = "₹"
    ) -> List[Dict[str, Any]]:
        """
        Format catalogue products into Meta Send API generic template carousel elements.
        Maximum 10 elements supported by Meta Messenger/Instagram Send API.
        """
        elements = []
        for prod in products[:10]:
            image_url = prod.images[0].image_url if getattr(prod, "images", None) else None
            price_val = getattr(prod, "price", 0.0)
            purity = getattr(prod, "gold_purity", "Pure Gold") or "Pure Gold"
            subtitle = f"{currency_symbol}{price_val:,.0f} | {purity}"
            if getattr(prod, "gross_weight", None):
                subtitle += f" | {prod.gross_weight}g"

            elem = {
                "title": (prod.name or "Jewellery Item")[:80],
                "subtitle": subtitle[:80]
            }
            if image_url:
                elem["image_url"] = image_url
            elements.append(elem)
        return elements



instagram_client = InstagramClient()
