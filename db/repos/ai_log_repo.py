from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AIQueryLog


async def add(
    session: AsyncSession,
    user_id: int,
    question: str,
    answer: str | None = None,
    intent: str | None = None,
) -> AIQueryLog:
    log = AIQueryLog(user_id=user_id, question=question, answer=answer, intent=intent)
    session.add(log)
    await session.flush()
    return log


async def get_last_n(session: AsyncSession, user_id: int, n: int = 10) -> list[AIQueryLog]:
    """Возвращает последние n обменов в хронологическом порядке."""
    result = await session.execute(
        select(AIQueryLog)
        .where(AIQueryLog.user_id == user_id)
        .order_by(AIQueryLog.created_at.desc())
        .limit(n)
    )
    return list(reversed(result.scalars().all()))


async def count_today(session: AsyncSession, user_id: int) -> int:
    today = datetime.now(timezone.utc).date()
    result = await session.execute(
        select(func.count()).where(
            AIQueryLog.user_id == user_id,
            func.date(AIQueryLog.created_at) == today,
        )
    )
    return result.scalar_one()
