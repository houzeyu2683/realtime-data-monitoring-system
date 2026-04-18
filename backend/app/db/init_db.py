from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.db.session import AsyncSessionLocal


async def init_db() -> None:
    async with AsyncSessionLocal() as session:
        await _create_default_admin(session)


async def _create_default_admin(session: AsyncSession) -> None:
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.username == "admin"))
    if result.scalar_one_or_none():
        return

    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hash_password("admin1234"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.add(admin)
    await session.commit()
