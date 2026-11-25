"""Client-facing authentication and OAuth regression checks. No live Meta calls."""
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from app.core.config import settings
from app.core.security import create_access_token, create_oauth_state
from app.models.models import InstagramAccount, User
from app.services.instagram.oauth import instagram_oauth


def test_browser_session_login_and_logout(unauthenticated_client):
    client = unauthenticated_client
    response = client.post("/api/v1/auth/login", json={
        "email": "owner@jewelai.com", "password": "testpass123",
    })
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 403
    assert client.post("/api/v1/auth/logout", headers={
        "X-JewelAI-Request": "1", "Origin": "https://attacker.example",
    }).status_code == 403
    assert client.post("/api/v1/auth/logout", headers={"X-JewelAI-Request": "1"}).status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


def test_inactive_users_cannot_sign_in(unauthenticated_client, db_session):
    user = db_session.query(User).filter_by(email="owner@jewelai.com").one()
    user.is_active = False
    db_session.commit()
    try:
        assert unauthenticated_client.post("/api/v1/auth/login", json={
            "email": user.email, "password": "testpass123",
        }).status_code == 401
        token = create_access_token({"sub": user.id})
        assert unauthenticated_client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {token}",
        }).status_code == 401
    finally:
        user.is_active = True
        db_session.commit()


def test_oauth_state_is_required(client):
    assert client.post("/api/v1/auth/instagram/connect", json={"code": "example"}).status_code == 422


def test_oauth_state_is_bound_to_browser(client, db_session):
    user = db_session.query(User).first()
    state = create_oauth_state(user.id)
    response = client.post("/api/v1/auth/instagram/connect", json={"code": "example", "state": state})
    assert response.status_code == 400
    assert "state" in response.json()["detail"].lower()


def test_oauth_not_configured_is_actionable(client, monkeypatch):
    monkeypatch.setattr(instagram_oauth, "app_id", "")
    response = client.get("/api/v1/auth/instagram/oauth-url")
    assert response.status_code == 503
    assert "administrator" in response.json()["detail"].lower()


def test_instagram_sign_in_existing_connection(unauthenticated_client, db_session, monkeypatch):
    client = unauthenticated_client
    user = db_session.query(User).filter_by(email="owner@jewelai.com").one()
    account = db_session.query(InstagramAccount).filter_by(user_id=user.id).first()
    monkeypatch.setattr(instagram_oauth, "app_id", "test-app-id")

    async def exchange(*args, **kwargs):
        return {"access_token": "short-token"}

    async def long_token(*args, **kwargs):
        return {"access_token": "long-token", "expires_in": 5184000}

    async def profile(*args, **kwargs):
        return {"user_id": account.ig_user_id, "username": account.username}

    monkeypatch.setattr(instagram_oauth, "exchange_code_for_short_lived_token", exchange)
    monkeypatch.setattr(instagram_oauth, "exchange_for_long_lived_token", long_token)
    monkeypatch.setattr(instagram_oauth, "get_instagram_profile", profile)
    start = client.get("/api/v1/auth/instagram/login")
    assert start.status_code == 200
    state = start.json()["state"]
    query = parse_qs(urlparse(start.json()["url"]).query)
    assert "instagram_business_manage_comments" in query["scope"][0]
    assert client.post("/api/v1/auth/instagram/session", json={
        "code": "test-code", "state": state,
    }).status_code == 200
    assert client.get("/api/v1/auth/me").json()["id"] == user.id
    db_session.refresh(account)
    expiry = account.token_expires_at.replace(tzinfo=timezone.utc)
    assert expiry > datetime.now(timezone.utc)
    # A consumed callback cannot be re-used, even from the same browser.
    assert client.post("/api/v1/auth/instagram/session", json={
        "code": "test-code", "state": state,
    }, headers={"X-JewelAI-Request": "1"}).status_code == 400


def test_unknown_instagram_does_not_bypass_registration(unauthenticated_client, monkeypatch):
    monkeypatch.setattr(instagram_oauth, "app_id", "test-app-id")

    async def exchange(*args, **kwargs):
        return {"access_token": "token", "expires_in": 5184000}

    async def profile(*args, **kwargs):
        return {"user_id": "not-linked-to-any-workspace", "username": "new_client"}

    monkeypatch.setattr(instagram_oauth, "exchange_code_for_short_lived_token", exchange)
    monkeypatch.setattr(instagram_oauth, "exchange_for_long_lived_token", exchange)
    monkeypatch.setattr(instagram_oauth, "get_instagram_profile", profile)
    start = unauthenticated_client.get("/api/v1/auth/instagram/login").json()
    response = unauthenticated_client.post("/api/v1/auth/instagram/session", json={
        "code": "example", "state": start["state"],
    })
    assert response.status_code == 409
    assert unauthenticated_client.get("/api/v1/auth/me").status_code == 401


def test_production_disallows_mock_integrations():
    from app.core.config import Settings
    import pytest
    from pydantic import ValidationError
    from cryptography.fernet import Fernet

    with pytest.raises(ValidationError, match="mock"):
        Settings(_env_file=None, ENVIRONMENT="production", DEBUG=False,
                 SECRET_KEY="a-unique-production-secret-at-least-32-characters",
                 ENCRYPTION_KEY=Fernet.generate_key().decode(), MOCK_INSTAGRAM_API=True)
