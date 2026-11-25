import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
import bcrypt
import jwt
from jwt import InvalidTokenError
from cryptography.fernet import Fernet
from app.core.config import settings

# Fernet cipher instance for symmetric token encryption
_fernet_instance: Optional[Fernet] = None


def get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        if not settings.ENCRYPTION_KEY:
            raise ValueError(
                "ENCRYPTION_KEY environment variable is missing or empty. "
                "A stable 32-byte url-safe base64 Fernet key must be configured in environment."
            )
        try:
            key = settings.ENCRYPTION_KEY.encode()
            _fernet_instance = Fernet(key)
        except Exception as e:
            raise ValueError(
                f"Invalid ENCRYPTION_KEY configured: {e}. "
                "Generating random keys on restart is prohibited as it causes stored token decryption failure."
            )
    return _fernet_instance


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt (truncated to 72 bytes)."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return payload
    except InvalidTokenError:
        return None


def encrypt_token(raw_token: str) -> str:
    """Encrypt sensitive OAuth tokens for storage at rest."""
    if not raw_token:
        return ""
    fernet = get_fernet()
    encrypted = fernet.encrypt(raw_token.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt stored access tokens."""
    if not encrypted_token:
        return ""
    fernet = get_fernet()
    decrypted = fernet.decrypt(encrypted_token.encode("utf-8"))
    return decrypted.decode("utf-8")


def verify_meta_webhook_signature(payload_bytes: bytes, signature_header: Optional[str], secret: Optional[str] = None) -> bool:
    """
    Verify Meta Instagram X-Hub-Signature-256 header.
    Format is 'sha256=<hex_digest>'.
    In production, signature is mandatory and strictly verified.
    """
    app_secret = secret or settings.INSTAGRAM_APP_SECRET
    if not app_secret:
        if settings.ENVIRONMENT != "production" and settings.DEBUG and not signature_header:
            return True
        return False
        
    if not signature_header or not signature_header.startswith("sha256="):
        return False
        
    expected_hash = signature_header[7:]
    calculated_hash = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_hash, calculated_hash)


def create_oauth_state(user_id: str, expires_in_seconds: int = 900) -> str:
    """
    Generate a cryptographically signed state token for Instagram OAuth to prevent CSRF.
    Contains user_id, expiry timestamp, random nonce, and HMAC-SHA256 signature.
    """
    import secrets
    import time
    expiry = int(time.time()) + expires_in_seconds
    nonce = secrets.token_hex(8)
    message = f"{user_id}:{expiry}:{nonce}"
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return f"{message}:{signature}"


def verify_oauth_state(state: str, expected_user_id: str, max_drift_seconds: int = 60) -> bool:
    """
    Validate an Instagram OAuth state token.
    Ensures user_id matches, token is not expired, and signature is authentic.
    """
    import time
    if not state or ":" not in state:
        return False
    parts = state.split(":")
    if len(parts) != 4:
        return False
    
    user_id, expiry_str, nonce, signature = parts
    if user_id != expected_user_id:
        return False
        
    try:
        expiry = int(expiry_str)
    except ValueError:
        return False
        
    # Check expiry
    current_time = int(time.time())
    if current_time > expiry:
        return False
        
    # Verify HMAC signature
    message = f"{user_id}:{expiry_str}:{nonce}"
    expected_sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_sig, signature)
