from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AIQueryLog


async def add(
    session: AsyncSession,
    user_id: int,
    question: str,
    intent: str | None = None,
) -> AIQueryLog:
    log = AIQueryLog(user_id=user_id, question=question, intent=intent)
    session.add(log)
    await session.flush()
    return log


async def count_today(session: AsyncSession, user_id: int) -> int:
    today = datetime.now(timezone.utc).date()
    result = await session.execute(
        select(func.count()).where(
            AIQueryLog.user_id == user_id,
            func.date(AIQueryLog.created_at) == today,
        )
    )
    return result.scalar_one()
