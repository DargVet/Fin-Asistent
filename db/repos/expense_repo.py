from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ExpenseRegular, ExpenseIrregular


async def get_regular(session: AsyncSession, user_id: int) -> list[ExpenseRegular]:
    result = await session.execute(
        select(ExpenseRegular).where(ExpenseRegular.user_id == user_id)
    )
    return list(result.scalars().all())


async def add_regular(
    session: AsyncSession,
    user_id: int,
    name: str,
    amount: float,
    charge_day: int,
) -> ExpenseRegular:
    item = ExpenseRegular(user_id=user_id, name=name, amount=amount, charge_day=charge_day)
    session.add(item)
    await session.flush()
    return item


async def delete_regular(session: AsyncSession, expense_id: int) -> None:
    item = await session.get(ExpenseRegular, expense_id)
    if item:
        await session.delete(item)


async def get_irregular(
    session: AsyncSession, user_id: int, from_date: date, to_date: date
) -> list[ExpenseIrregular]:
    result = await session.execute(
        select(ExpenseIrregular).where(
            ExpenseIrregular.user_id == user_id,
            ExpenseIrregular.spent_at >= from_date,
            ExpenseIrregular.spent_at <= to_date,
        )
    )
    return list(result.scalars().all())


async def add_irregular(
    session: AsyncSession,
    user_id: int,
    category: str,
    amount: float,
    is_mandatory: bool = False,
) -> ExpenseIrregular:
    item = ExpenseIrregular(
        user_id=user_id, category=category, amount=amount, is_mandatory=is_mandatory
    )
    session.add(item)
    await session.flush()
    return item
