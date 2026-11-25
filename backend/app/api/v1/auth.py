from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
import hmac
import logging

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, encrypt_token
)
from app.core.rate_limit import auth_rate_limiter
from app.models.models import User, InstagramAccount, BusinessSettings
from app.schemas.schemas import (
    UserLogin, UserCreate, UserResponse,
    TokenResponse, InstagramAccountResponse, InstagramConnectRequest,
    InstagramConnectTokenRequest
)
from app.api.deps import get_current_user, get_current_instagram_account
from app.services.instagram.oauth import instagram_oauth

logger = logging.getLogger(__name__)
router = APIRouter()


def issue_session(response: Response, user: User):
    token = create_access_token({"sub": user.id})
    response.set_cookie(
        "jewelai_session", token, httponly=True, samesite="lax",
        secure=settings.ENVIRONMENT == "production",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/",
    )
    return {"access_token": token, "token_type": "bearer", "user": user}


def begin_oauth(response: Response, user_id: str):
    if not instagram_oauth.app_id or not instagram_oauth.app_secret:
        raise HTTPException(503, "Instagram sign-in is not configured yet. Please contact your administrator.")
    data = instagram_oauth.get_authorization_url(user_id=user_id)
    response.set_cookie(
        "jewelai_oauth_state", data["state"], httponly=True, samesite="lax",
        secure=settings.ENVIRONMENT == "production", max_age=900, path="/api/v1/auth/instagram",
    )
    return data


def validate_callback(data: InstagramConnectRequest, request: Request, user_id: str):
    cookie_state = request.cookies.get("jewelai_oauth_state", "")
    if not hmac.compare_digest(data.state, cookie_state) or not instagram_oauth.verify_state(data.state, user_id):
        raise HTTPException(400, "Invalid or expired OAuth state token. Please start Instagram sign-in again.")
    if data.redirect_uri and data.redirect_uri != instagram_oauth.redirect_uri:
        raise HTTPException(400, "Instagram redirect address does not match this application.")


async def exchange_instagram_code(data: InstagramConnectRequest):
    try:
        short = await instagram_oauth.exchange_code_for_short_lived_token(code=data.code)
        long = await instagram_oauth.exchange_for_long_lived_token(short["access_token"])
        token = long["access_token"]
        profile = await instagram_oauth.get_instagram_profile(token)
        if not (profile.get("user_id") or profile.get("id")) or not profile.get("username"):
            raise ValueError("Incomplete Instagram profile")
        return token, profile, long.get("expires_in")
    except Exception as exc:
        logger.warning("Instagram authorization failed (%s)", type(exc).__name__)
        raise HTTPException(502, "Instagram could not finish authorization. Please try connecting again.") from exc


async def save_connection(db: Session, user: User, token: str, profile: dict, expires_in=None):
    ig_user_id = str(profile.get("user_id") or profile.get("id") or "")
    if not ig_user_id or not profile.get("username"):
        raise HTTPException(400, "Instagram did not return a valid professional account.")
    linked = db.query(InstagramAccount).filter_by(ig_user_id=ig_user_id).first()
    if linked and linked.user_id != user.id:
        raise HTTPException(409, "This Instagram account is already linked to another workspace. Contact your administrator.")
    account = db.query(InstagramAccount).filter_by(user_id=user.id).first()
    if account and account.ig_user_id != ig_user_id:
        # Never mix the old account's conversations and inventory with a different business.
        raise HTTPException(409, "Please reconnect the original Instagram account. A different business needs its own workspace.")
    try:
        subscribed = await instagram_oauth.subscribe_app_to_webhooks(token)
    except Exception as exc:
        logger.warning("Instagram webhook subscription failed (%s)", type(exc).__name__)
        subscribed = False
    if not subscribed:
        raise HTTPException(502, "Instagram permissions could not be enabled. Reconnect and allow messaging and comment access.")
    if not account:
        account = InstagramAccount(user_id=user.id, ig_user_id=ig_user_id)
        db.add(account)
        account.settings = BusinessSettings(
            business_name=profile.get("name") or profile["username"],
            auto_reply_enabled=False,
        )
    account.username = profile["username"]
    account.name = profile.get("name") or profile["username"]
    account.profile_pic_url = profile.get("profile_picture_url")
    account.token_encrypted = encrypt_token(token)
    account.is_connected = True
    account.webhook_subscribed = True
    account.last_synced_at = datetime.now(timezone.utc)
    account.token_expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=int(expires_in)) if expires_in else None
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "This Instagram account is already connected. Please refresh and try again.") from exc
    db.refresh(account)
    return account


@router.post("/register", response_model=TokenResponse)
def register(user_in: UserCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    auth_rate_limiter.check(request, "register")

    # Invite-only signup enforcement: first user becomes owner, subsequent users must provide valid invite
    user_count = db.query(User).count()
    if not settings.ENABLE_OPEN_REGISTRATION and (user_count > 0 or settings.ENVIRONMENT == "production"):
        if not user_in.invite_code or not hmac.compare_digest(user_in.invite_code.strip(), settings.REGISTRATION_INVITE_CODE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration is invite-only. A valid invite code is required."
            )

    email = str(user_in.email).lower()
    existing = db.query(User).filter(func.lower(User.email) == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    assigned_role = "owner" if user_count == 0 else "staff"

    user = User(
        name=user_in.name,
        email=email,
        password_hash=hash_password(user_in.password),
        role=assigned_role
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists. Please sign in.") from exc
    db.refresh(user)

    return issue_session(response, user)


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    auth_rate_limiter.check(request, "login")

    user = db.query(User).filter(func.lower(User.email) == str(login_data.email).lower()).first()
    if not user or not user.is_active or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    return issue_session(response, user)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("jewelai_session", path="/")
    response.delete_cookie("jewelai_oauth_state", path="/api/v1/auth/instagram")
    return {"message": "You have been signed out."}


@router.get("/setup")
def setup_status(db: Session = Depends(get_db)):
    return {
        "registration_requires_invite": not settings.ENABLE_OPEN_REGISTRATION and (
            settings.ENVIRONMENT == "production" or db.query(User).count() > 0
        ),
        "instagram_login_available": bool(instagram_oauth.app_id and instagram_oauth.app_secret),
    }


@router.get("/instagram/status")
def instagram_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(InstagramAccount).filter_by(user_id=current_user.id).first()
    return {
        "account": InstagramAccountResponse.model_validate(account) if account else None,
        "login_available": bool(instagram_oauth.app_id and instagram_oauth.app_secret),
    }


@router.get("/instagram/login")
def instagram_login(request: Request, response: Response):
    auth_rate_limiter.check(request, "instagram_login")
    return begin_oauth(response, "login")


@router.get("/instagram/oauth-url")
def get_instagram_oauth_url(response: Response, current_user: User = Depends(get_current_user)):
    return begin_oauth(response, current_user.id)


@router.post("/instagram/session", response_model=TokenResponse)
async def instagram_session(data: InstagramConnectRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    auth_rate_limiter.check(request, "instagram_session")
    validate_callback(data, request, "login")
    token, profile, expires_in = await exchange_instagram_code(data)
    ig_id = str(profile.get("user_id") or profile.get("id"))
    account = db.query(InstagramAccount).filter_by(ig_user_id=ig_id, is_connected=True).first()
    if not account:
        raise HTTPException(409, "This Instagram account is not linked yet. Sign in with your workspace email, then connect Instagram once.")
    user = db.query(User).filter_by(id=account.user_id, is_active=True).first()
    if not user:
        raise HTTPException(401, "This workspace is inactive. Contact your administrator.")
    await save_connection(db, user, token, profile, expires_in)
    response.delete_cookie("jewelai_oauth_state", path="/api/v1/auth/instagram")
    return issue_session(response, user)


@router.post("/instagram/connect", response_model=InstagramAccountResponse)
async def connect_instagram(
    data: InstagramConnectRequest,
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    validate_callback(data, request, current_user.id)
    token, profile, expires_in = await exchange_instagram_code(data)
    account = await save_connection(db, current_user, token, profile, expires_in)
    response.delete_cookie("jewelai_oauth_state", path="/api/v1/auth/instagram")
    return account


@router.post("/instagram/connect-token", response_model=InstagramAccountResponse)
async def connect_instagram_token(
    data: InstagramConnectTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Retained only for explicitly enabled operator recovery and isolated tests.
    if not settings.ENABLE_DIRECT_TOKEN_CONNECT and settings.ENVIRONMENT != "test":
        raise HTTPException(404, "Please use Sign in with Instagram to connect your account.")
    token = data.access_token.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access token cannot be empty."
        )

    try:
        profile = await instagram_oauth.get_instagram_profile(token)
    except Exception as exc:
        raise HTTPException(502, "Instagram could not verify this connection.") from exc
    return await save_connection(db, current_user, token, profile)


@router.post("/instagram/disconnect")
def disconnect_instagram(
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    account.is_connected = False
    account.token_encrypted = ""
    account.webhook_subscribed = False
    account.token_expires_at = None
    if account.settings:
        account.settings.auto_reply_enabled = False
    db.commit()
    return {"message": "Instagram account disconnected successfully."}
