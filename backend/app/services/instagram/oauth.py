import httpx
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from app.core.config import settings
from app.core.security import create_oauth_state, verify_oauth_state

logger = logging.getLogger(__name__)


class InstagramOAuthService:
    """
    Official Meta Instagram Platform OAuth 2.0 implementation with Instagram Login.
    References:
    - https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login
    - https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login-for-instagram
    - Graph API v22.0
    """

    def __init__(self):
        self.app_id = settings.INSTAGRAM_APP_ID
        self.app_secret = settings.INSTAGRAM_APP_SECRET
        self.redirect_uri = settings.INSTAGRAM_REDIRECT_URI
        self.oauth_dialog_url = "https://www.instagram.com/oauth/authorize"
        self.token_exchange_url = "https://api.instagram.com/oauth/access_token"
        self.graph_base_url = settings.META_GRAPH_URL
        self.api_version = settings.META_API_VERSION

    def get_authorization_url(self, user_id: str, redirect_uri: Optional[str] = None) -> Dict[str, str]:
        """
        Build the official Meta Instagram OAuth dialog URL with business permissions
        and a cryptographically signed HMAC state token to prevent CSRF attacks.
        Scopes:
        - instagram_business_basic: Public profile & media
        - instagram_business_manage_messages: Send & receive direct messages
        """
        state = create_oauth_state(user_id=user_id)
        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri or self.redirect_uri,
            "scope": "instagram_business_basic,instagram_business_manage_messages,instagram_business_manage_comments",
            "enable_fb_login": "0",
            "response_type": "code",
            "state": state
        }
        return {
            "url": f"{self.oauth_dialog_url}?{urlencode(params)}",
            "state": state
        }

    def verify_state(self, state: str, user_id: str) -> bool:
        """Verify the cryptographically signed OAuth state token."""
        return verify_oauth_state(state=state, expected_user_id=user_id)

    async def exchange_code_for_short_lived_token(
        self,
        code: str,
        redirect_uri: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange the authorization code for a short-lived user access token.
        POST https://api.instagram.com/oauth/access_token
        """
        if settings.MOCK_INSTAGRAM_API or settings.ENVIRONMENT == "test":
            return {
                "access_token": "test_short_lived_token",
                "user_id": "17841400000000001",
                "permissions": ["instagram_business_basic", "instagram_business_manage_messages", "instagram_business_manage_comments"],
            }

        if not self.app_id or not self.app_secret:
            raise ValueError(
                "INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET must be configured in environment for Meta OAuth."
            )

        data = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri or self.redirect_uri,
            "code": code
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(self.token_exchange_url, data=data)
            if response.status_code != 200:
                raise ValueError("Instagram authorization code exchange failed.")
            data = response.json()
            # Meta responses may wrap the access token in a single-item data array.
            return data["data"][0] if isinstance(data.get("data"), list) else data

    async def exchange_for_long_lived_token(
        self,
        short_lived_token: str
    ) -> Dict[str, Any]:
        """
        Exchange a short-lived token for a long-lived 60-day token.
        GET https://graph.instagram.com/access_token
        """
        if settings.MOCK_INSTAGRAM_API or settings.ENVIRONMENT == "test":
            return {"access_token": "test_long_lived_token", "token_type": "bearer", "expires_in": 5184000}

        if not self.app_secret:
            raise ValueError("INSTAGRAM_APP_SECRET is required for long-lived token exchange.")

        url = f"{self.graph_base_url}/access_token"
        params = {
            "grant_type": "ig_exchange_token",
            "client_secret": self.app_secret,
            "access_token": short_lived_token
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                raise ValueError("Instagram long-lived token exchange failed.")
            return response.json()

    async def get_instagram_profile(self, access_token: str) -> Dict[str, Any]:
        """
        Fetch the verified Instagram Professional account profile details.
        GET https://graph.instagram.com/{api_version}/me?fields=id,user_id,username,name,profile_picture_url
        """
        if settings.MOCK_INSTAGRAM_API or settings.ENVIRONMENT == "test":
            return {
                "id": "17841400001234567",
                "user_id": "17841400001234567",
                "username": "jewellery_client_official",
                "name": "Official Fine Jewellery Client",
                "profile_picture_url": ""
            }

        url = f"{self.graph_base_url}/{self.api_version}/me"
        params = {
            "fields": "id,user_id,username,name,profile_picture_url",
            "access_token": access_token
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                raise ValueError("Instagram profile could not be verified.")
            return response.json()

    async def subscribe_app_to_webhooks(self, access_token: str) -> bool:
        """
        Subscribe the Meta app to webhooks for this Instagram account.
        POST https://graph.instagram.com/{api_version}/me/subscribed_apps
        subscribed_fields: messages, messaging_postbacks, message_reactions
        """
        if settings.MOCK_INSTAGRAM_API or settings.ENVIRONMENT == "test":
            logger.info("[TEST/MOCK] App webhook subscribed simulated successfully")
            return True

        url = f"{self.graph_base_url}/{self.api_version}/me/subscribed_apps"
        params = {
            "subscribed_fields": "messages,messaging_postbacks,message_reactions,comments",
            "access_token": access_token
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, params=params)
            if response.status_code != 200:
                logger.warning("Meta webhook subscription returned status %s", response.status_code)
                # Some Instagram business setups use Graph API v22.0 user-level subscriptions
                return False
            data = response.json()
            return data.get("success") is True


instagram_oauth = InstagramOAuthService()
