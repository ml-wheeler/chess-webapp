import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def new_secret() -> str:
    return secrets.token_urlsafe(32)


def digest_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def expires_in(hours: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def as_utc(value: datetime) -> datetime:
    # SQLite may return naive datetimes even when timezone=True.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
