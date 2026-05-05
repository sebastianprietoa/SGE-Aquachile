import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt

from app.core.config import get_settings


def _derive_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = _derive_password(password, salt)
    return f"{salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_password: str) -> bool:
    try:
        salt_hex, derived_hex = stored_password.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(derived_hex)
    except ValueError:
        return False
    candidate = _derive_password(password, salt)
    return hmac.compare_digest(candidate, expected)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload: Dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

