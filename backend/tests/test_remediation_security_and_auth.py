import pytest
import time
from fastapi.testclient import TestClient
from app.core.security import (
    create_access_token, create_oauth_state, verify_oauth_state
)
from app.models.models import User, InstagramAccount
from app.services.instagram.oauth import instagram_oauth
from app.services.instagram.client import InstagramClient


def test_auth_bypass_prevented_without_token(unauthenticated_client: TestClient):
    """
    CRITICAL: Verify that requests without a Bearer token are rejected with 401 Unauthorized.
    Proves the removal of the dev auto-login bypass.
    """
    # Protected endpoints must strictly return 401
    res_me = unauthenticated_client.get("/api/v1/auth/me")
    assert res_me.status_code == 401
    assert "detail" in res_me.json()

    res_products = unauthenticated_client.get("/api/v1/products")
    assert res_products.status_code == 401

    res_settings = unauthenticated_client.get("/api/v1/settings")
    assert res_settings.status_code == 401


def test_invalid_jwt_token_rejected(unauthenticated_client: TestClient):
    """Verify that forged or malformed JWT tokens are rejected with 401."""
    res = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.invalid.signature"}
    )
    assert res.status_code == 401


def test_valid_jwt_token_accepted(unauthenticated_client: TestClient, db_session):
    """Verify that valid signed JWT tokens authenticate successfully."""
    user = db_session.query(User).filter(User.email == "owner@jewelai.com").first()
    token = create_access_token({"sub": user.id})

    res = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "owner@jewelai.com"
    assert data["id"] == user.id


def test_oauth_state_generation_and_tampering_defense():
    """Verify cryptographic HMAC-SHA256 OAuth state token generation and verification."""
    user_id = "usr_jewel_001"
    state = create_oauth_state(user_id=user_id, expires_in_seconds=600)
    
    # 1. Valid state matches expected user
    assert verify_oauth_state(state=state, expected_user_id=user_id) is True

    # 2. State rejected for different user ID (CSRF mismatch)
    assert verify_oauth_state(state=state, expected_user_id="usr_attacker_999") is False

    # 3. Tampered nonce or timestamp rejected
    parts = state.split(":")
    tampered_parts = [parts[0], str(int(parts[1]) + 100), parts[2], parts[3]]
    tampered_state = ":".join(tampered_parts)
    assert verify_oauth_state(state=tampered_state, expected_user_id=user_id) is False

    # 4. Tampered signature rejected
    bad_sig_state = f"{parts[0]}:{parts[1]}:{parts[2]}:00000000000000000000000000000000"
    assert verify_oauth_state(state=bad_sig_state, expected_user_id=user_id) is False

    # 5. Expired state token rejected
    expired_state = create_oauth_state(user_id=user_id, expires_in_seconds=-10)
    assert verify_oauth_state(state=expired_state, expected_user_id=user_id) is False


def test_instagram_connect_rejects_tampered_state(client: TestClient):
    """Verify that /auth/instagram/connect rejects requests with an invalid OAuth state."""
    res = client.post(
        "/api/v1/auth/instagram/connect",
        json={
            "code": "sample_auth_code_123",
            "state": "forged:user:timestamp:badhash"
        }
    )
    assert res.status_code == 400
    assert "state token" in res.json()["detail"].lower()


def test_no_connected_account_returns_404_not_fake_account(unauthenticated_client: TestClient, db_session):
    """
    Verify that an authenticated user without an Instagram connection receives a 404
    and is NEVER automatically seeded with a fake account or fake products.
    """
    from app.core.security import hash_password
    new_user = User(
        name="New Jewellery Client",
        email="newclient@jewellery.com",
        password_hash=hash_password("securepass123"),
        role="owner"
    )
    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)

    token = create_access_token({"sub": new_user.id})

    # Calling catalogue or settings requires an Instagram account
    res = unauthenticated_client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 404
    assert "No connected Instagram account found" in res.json()["detail"]

    # Verify no fake account was created in the database
    account = db_session.query(InstagramAccount).filter(InstagramAccount.user_id == new_user.id).first()
    assert account is None


def test_connect_instagram_token_endpoint(unauthenticated_client: TestClient, db_session):
    """
    Verify that an authenticated user can connect an Instagram account directly with an access token,
    encrypting the token, syncing the profile, and establishing webhook subscription.
    """
    from app.core.security import hash_password, decrypt_token
    user = User(
        name="Direct Token Jeweller",
        email="directtoken@jewelai.com",
        password_hash=hash_password("securepass123"),
        role="owner"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    auth_token = create_access_token({"sub": user.id})

    # Test empty token validation
    res_empty = unauthenticated_client.post(
        "/api/v1/auth/instagram/connect-token",
        json={"access_token": ""},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert res_empty.status_code == 400

    # Test connecting with valid token (mock/test mode profile exchange)
    res_success = unauthenticated_client.post(
        "/api/v1/auth/instagram/connect-token",
        json={"access_token": "test_direct_access_token_12345678"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert res_success.status_code == 200
    data = res_success.json()
    assert data["is_connected"] is True
    assert data["webhook_subscribed"] is True

    # Verify encrypted in database
    db_acc = db_session.query(InstagramAccount).filter(InstagramAccount.user_id == user.id).first()
    assert db_acc is not None
    assert decrypt_token(db_acc.token_encrypted) == "test_direct_access_token_12345678"
