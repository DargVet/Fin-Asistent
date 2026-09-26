from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import IncomeRegular, IncomeIrregular


async def get_regular(session: AsyncSession, user_id: int) -> list[IncomeRegular]:
    result = await session.execute(
        select(IncomeRegular).where(IncomeRegular.user_id == user_id)
    )
    return list(result.scalars().all())


async def add_regular(
    session: AsyncSession,
    user_id: int,
    source: str,
    amount: float,
    pay_day: int,
    frequency: str = "monthly",
) -> IncomeRegular:
    item = IncomeRegular(
        user_id=user_id, source=source, amount=amount,
        pay_day=pay_day, frequency=frequency,
    )
    session.add(item)
    await session.flush()
    return item


async def update_regular_amount(session: AsyncSession, income_id: int, amount: float) -> None:
    item = await session.get(IncomeRegular, income_id)
    if item:
        item.amount = amount


async def delete_regular(session: AsyncSession, income_id: int) -> None:
    item = await session.get(IncomeRegular, income_id)
    if item:
        await session.delete(item)


async def get_all_irregular(session: AsyncSession, user_id: int) -> list[IncomeIrregular]:
    result = await session.execute(
        select(IncomeIrregular).where(IncomeIrregular.user_id == user_id)
    )
    return list(result.scalars().all())


async def get_irregular(
    session: AsyncSession, user_id: int, from_date: date, to_date: date
) -> list[IncomeIrregular]:
    from sqlalchemy import func as sqlfunc
    result = await session.execute(
        select(IncomeIrregular).where(
            IncomeIrregular.user_id == user_id,
            sqlfunc.date(IncomeIrregular.received_at) >= from_date,
            sqlfunc.date(IncomeIrregular.received_at) <= to_date,
        )
    )
    return list(result.scalars().all())


async def add_irregular(
    session: AsyncSession, user_id: int, source: str, amount: float
) -> IncomeIrregular:
    item = IncomeIrregular(user_id=user_id, source=source, amount=amount)
    session.add(item)
    await session.flush()
    return item
