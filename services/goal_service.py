from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Goal
from db.repos import goal_repo


async def create(
    session: AsyncSession,
    user_id: int,
    name: str,
    target_amount: float,
    deadline: date | None = None,
) -> Goal:
    goal = await goal_repo.create(session, user_id, name, target_amount, deadline)
    await session.commit()
    return goal


async def get_all(session: AsyncSession, user_id: int) -> list[Goal]:
    return await goal_repo.get_all(session, user_id)


async def add_savings(session: AsyncSession, goal_id: int, amount: float) -> Goal | None:
    """Добавляет сумму к текущему накоплению по цели."""
    goal = await goal_repo.get_by_id(session, goal_id)
    if not goal:
        return None
    new_amount = float(goal.current_amount) + amount
    updated = await goal_repo.update_current_amount(session, goal_id, new_amount)
    await session.commit()
    return updated


async def delete(session: AsyncSession, goal_id: int) -> None:
    await goal_repo.delete(session, goal_id)
    await session.commit()
