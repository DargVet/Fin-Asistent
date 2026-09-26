from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, Balance, IncomeRegular, IncomeIrregular
from db.models import ExpenseRegular, ExpenseIrregular, Goal, AIQueryLog
from db.repos import user_repo


async def get_or_create(session: AsyncSession, telegram_id: int) -> User:
    """Возвращает существующего пользователя или создаёт нового."""
    user = await user_repo.get_by_telegram_id(session, telegram_id)
    if not user:
        user = await user_repo.create(session, telegram_id)
        await session.commit()
    return user


async def clear_all_data(session: AsyncSession, user_id: int) -> None:
    """Удаляет все финансовые данные пользователя, сохраняя аккаунт."""
    for model in (IncomeRegular, IncomeIrregular, ExpenseRegular,
                  ExpenseIrregular, Goal, AIQueryLog, Balance):
        await session.execute(delete(model).where(model.user_id == user_id))
    await session.commit()
