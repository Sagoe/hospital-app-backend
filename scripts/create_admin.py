"""
One-off CLI script to bootstrap an admin account directly against the
database, bypassing the public /auth/register endpoint (which only
allows PATIENT self-registration). Run this locally/manually — it is
never exposed over HTTP.

Usage:
    python -m scripts.create_admin
"""

import asyncio
import getpass

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.enums import UserRole
from app.repositories.user_repository import UserRepository


async def main() -> None:
    email = input("Admin email: ").strip()
    password = getpass.getpass("Admin password (input hidden): ").strip()
    confirm = getpass.getpass("Confirm password: ").strip()

    if password != confirm:
        print("Passwords do not match. Aborting.")
        return

    async with AsyncSessionLocal() as session:
        user_repository = UserRepository(session)

        existing = await user_repository.get_by_email(email)
        if existing is not None:
            print(f"A user with email {email} already exists (role={existing.role}). Aborting.")
            return

        password_hash = hash_password(password)
        user = await user_repository.create(
            email=email,
            password_hash=password_hash,
            role=UserRole.ADMIN,
        )
        await session.commit()

        print(f"Admin account created: {user.email} (userId={user.userId})")


if __name__ == "__main__":
    asyncio.run(main())