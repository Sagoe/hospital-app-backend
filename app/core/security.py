"""
Password hashing (bcrypt via passlib) and JWT access-token issuance /
verification (python-jose). Kept separate from encryption.py because
these protect *credentials and session integrity*, not PHI at rest —
different threat model, different primitives (bcrypt is a one-way KDF;
PHI encryption must be reversible).
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenError(Exception):
    """Raised when a JWT is missing, malformed, expired, or has an invalid signature."""


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _pwd_context.verify(plain_password, password_hash)


def create_access_token(
    *,
    subject: str,
    role: str,
    settings: Settings | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Issue a signed JWT access token.

    `subject` is the userId (string form of the UUID). `role` is embedded
    directly in the claims so downstream authorization dependencies
    (require_role) don't need a DB round-trip on every request.
    """
    settings = settings or get_settings()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.JWT_ACCESS_EXPIRATION_MINUTES)

    claims: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expires_at,
        "type": "access",
    }
    if extra_claims:
        claims.update(extra_claims)

    return jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise TokenError("Invalid or expired access token.") from exc

    if payload.get("type") != "access":
        raise TokenError("Token is not a valid access token.")

    return payload
