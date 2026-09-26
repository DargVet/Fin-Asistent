from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from db.repos import user_repo


async def get_or_create(session: AsyncSession, telegram_id: int) -> User:
    """Возвращает существующего пользователя или создаёт нового."""
    user = await user_repo.get_by_telegram_id(session, telegram_id)
    if not user:
        user = await user_repo.create(session, telegram_id)
        await session.commit()
    return user
