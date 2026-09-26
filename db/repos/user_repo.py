from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User


async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def create(session: AsyncSession, telegram_id: int) -> User:
    user = User(telegram_id=telegram_id)
    session.add(user)
    await session.flush()
    return user


async def set_plan(session: AsyncSession, user_id: int, plan: str) -> None:
    user = await session.get(User, user_id)
    if user:
        user.plan = plan
