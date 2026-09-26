from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Balance


async def get(session: AsyncSession, user_id: int) -> Balance | None:
    return await session.get(Balance, user_id)


async def upsert(session: AsyncSession, user_id: int, amount: float) -> Balance:
    balance = await session.get(Balance, user_id)
    if balance:
        balance.amount = amount
    else:
        balance = Balance(user_id=user_id, amount=amount)
        session.add(balance)
    await session.flush()
    return balance
