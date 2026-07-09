"""
User repository.

Repositories are the ONLY layer permitted to construct SQLAlchemy
statements. Services must go through here rather than importing
`AsyncSession`/`select` themselves, so query logic stays in one
reviewable place and is easy to swap or optimize independently of
business rules.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.userId == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        role: UserRole,
    ) -> User:
        user = User(email=email, passwordHash=password_hash, role=role)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def set_mfa_secret(self, user: User, mfa_secret: str) -> User:
        user.mfaSecret = mfa_secret
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def enable_mfa(self, user: User) -> User:
        user.isMfaEnabled = True
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def deactivate(self, user: User) -> User:
        user.isActive = False
        await self._session.flush()
        await self._session.refresh(user)
        return user
