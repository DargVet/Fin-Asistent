from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import PromoCode


async def get_active(session: AsyncSession) -> list[PromoCode]:
    """Возвращает все промокоды у которых срок не истёк (или без срока)."""
    today = date.today()
    result = await session.execute(
        select(PromoCode).where(
            or_(PromoCode.valid_until.is_(None), PromoCode.valid_until >= today)
        )
    )
    return list(result.scalars().all())


async def add(
    session: AsyncSession,
    organization: str,
    purpose: str,
    code: str,
    valid_until: date | None = None,
    advertiser: str | None = None,
    erid: str | None = None,
) -> PromoCode:
    promo = PromoCode(
        organization=organization, purpose=purpose, code=code,
        valid_until=valid_until, advertiser=advertiser, erid=erid,
    )
    session.add(promo)
    await session.flush()
    return promo
