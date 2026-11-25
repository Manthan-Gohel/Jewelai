import pytest
from app.core.security import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
    encrypt_token, decrypt_token,
    verify_meta_webhook_signature
)


def test_password_hashing():
    pwd = "LuxeSecurePassword2026!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_flow():
    user_id = "test-user-uuid-1234"
    token = create_access_token({"sub": user_id, "role": "owner"})
    assert isinstance(token, str)
    
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == user_id
    assert decoded["role"] == "owner"


def test_meta_oauth_token_encryption():
    raw_meta_token = "EAABwzLIXnjYBO7ZCZC2kM7Q9V5bL1xK9YqZ3uL8p1..."
    encrypted = encrypt_token(raw_meta_token)
    
    # Must never be stored in plaintext
    assert encrypted != raw_meta_token
    assert "EAABwz" not in encrypted
    
    # Must decrypt accurately
    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_meta_token


def test_jwt_requires_expiration_and_rejects_expired_tokens():
    import base64
    import hashlib
    import hmac
    import json
    from datetime import timedelta
    from app.core.config import settings

    def encode_part(value):
        return base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b"=")

    message = encode_part({"alg": "HS256", "typ": "JWT"}) + b"." + encode_part({"sub": "test-owner"})
    signature = base64.urlsafe_b64encode(hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).digest()).rstrip(b"=")
    assert decode_access_token((message + b"." + signature).decode()) is None
    assert decode_access_token(create_access_token({"sub": "test-owner"}, timedelta(seconds=-10))) is None


def test_meta_webhook_signature_verification():
    import hmac
    import hashlib

    secret = "meta_app_secret_test_xyz"
    payload = b'{"object":"instagram","entry":[{"id":"123"}]}'
    
    # Valid signature
    valid_hash = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    valid_header = f"sha256={valid_hash}"
    assert verify_meta_webhook_signature(payload, valid_header, secret=secret) is True

    # Tampered signature
    tampered_header = "sha256=1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    assert verify_meta_webhook_signature(payload, tampered_header, secret=secret) is False

    # Missing header
    assert verify_meta_webhook_signature(payload, None, secret=secret) is False
