"""
Auth service — registration, login, and MFA enrollment/verification.

This is the only service permitted to touch `passwordHash` / `mfaSecret`
directly (via the repository) and the only one that calls
`create_access_token`. Routers must never construct tokens themselves.
"""

import pyotp

from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import AuditActionType, UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import MfaEnrollResponse, TokenResponse, UserCreate, UserLoginRequest
from app.services.audit_service import AuditService


class AuthError(Exception):
    """Raised for any authentication/authorization failure surfaced to the router."""


class AuthService:
    def __init__(self, user_repository: UserRepository, audit_service: AuditService) -> None:
        self._user_repository = user_repository
        self._audit_service = audit_service

    async def register(self, payload: UserCreate) -> User:
        """Public self-registration — patients only. Staff accounts are
        provisioned exclusively via `register_staff` by an authenticated
        admin (see app/routers/admin_router.py)."""
        if payload.role != UserRole.PATIENT:
            raise AuthError("Self-registration is only available for patients.")

        existing = await self._user_repository.get_by_email(payload.email)
        if existing is not None:
            raise AuthError("An account with this email already exists.")

        password_hash = hash_password(payload.password)
        return await self._user_repository.create(
            email=payload.email,
            password_hash=password_hash,
            role=payload.role,
        )

    async def register_staff(self, payload: UserCreate) -> User:
        """Admin-only staff provisioning — allows any role, including
        DOCTOR, NURSE, and ADMIN. Callers must already be authenticated
        and authorized as ADMIN at the router level."""
        existing = await self._user_repository.get_by_email(payload.email)
        if existing is not None:
            raise AuthError("An account with this email already exists.")

        password_hash = hash_password(payload.password)
        return await self._user_repository.create(
            email=payload.email,
            password_hash=password_hash,
            role=payload.role,
        )

    async def login(self, payload: UserLoginRequest, ip_address: str) -> TokenResponse:
        user = await self._user_repository.get_by_email(payload.email)
        if user is None or not user.isActive:
            raise AuthError("Invalid credentials.")

        if not verify_password(payload.password, user.passwordHash):
            raise AuthError("Invalid credentials.")

        if user.isMfaEnabled:
            if payload.mfaCode is None:
                raise AuthError("MFA code is required for this account.")
            if user.mfaSecret is None or not pyotp.TOTP(user.mfaSecret).verify(payload.mfaCode):
                raise AuthError("Invalid MFA code.")

        await self._audit_service.record(
            performed_by_user_id=user.userId,
            action_type=AuditActionType.AUTH_LOGIN,
            target_record_id=user.userId,
            target_table="users",
            ip_address=ip_address,
        )

        settings_expiry_minutes = _access_token_minutes()
        token = create_access_token(subject=str(user.userId), role=user.role.value)
        return TokenResponse(accessToken=token, expiresInMinutes=settings_expiry_minutes)

    async def enroll_mfa(self, user: User) -> MfaEnrollResponse:
        secret = pyotp.random_base32()
        await self._user_repository.set_mfa_secret(user, secret)
        provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
            name=user.email, issuer_name="Hospital Web Application"
        )
        return MfaEnrollResponse(mfaSecret=secret, provisioningUri=provisioning_uri)

    async def verify_and_enable_mfa(self, user: User, mfa_code: str) -> None:
        if user.mfaSecret is None:
            raise AuthError("MFA has not been enrolled for this account yet.")
        if not pyotp.TOTP(user.mfaSecret).verify(mfa_code):
            raise AuthError("Invalid MFA code.")
        await self._user_repository.enable_mfa(user)


def _access_token_minutes() -> int:
    from app.core.config import get_settings

    return get_settings().JWT_ACCESS_EXPIRATION_MINUTES