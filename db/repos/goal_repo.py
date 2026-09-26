from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Goal


async def get_all(session: AsyncSession, user_id: int) -> list[Goal]:
    result = await session.execute(select(Goal).where(Goal.user_id == user_id))
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, goal_id: int) -> Goal | None:
    return await session.get(Goal, goal_id)


async def create(
    session: AsyncSession,
    user_id: int,
    name: str,
    target_amount: float,
    deadline: date | None = None,
) -> Goal:
    goal = Goal(user_id=user_id, name=name, target_amount=target_amount, deadline=deadline)
    session.add(goal)
    await session.flush()
    return goal


async def update_current_amount(
    session: AsyncSession, goal_id: int, amount: float
) -> Goal | None:
    goal = await session.get(Goal, goal_id)
    if goal:
        goal.current_amount = amount
    return goal


async def delete(session: AsyncSession, goal_id: int) -> None:
    goal = await session.get(Goal, goal_id)
    if goal:
        await session.delete(goal)
