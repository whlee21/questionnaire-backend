import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.admin import AdminUser


async def seed_admin() -> None:
    settings = get_settings()
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        print("ERROR: ADMIN_EMAIL and ADMIN_PASSWORD must be set in environment")
        sys.exit(1)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AdminUser).where(AdminUser.email == settings.ADMIN_EMAIL)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Admin already exists: {settings.ADMIN_EMAIL}")
            return

        admin = AdminUser(
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Created admin: {settings.ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
