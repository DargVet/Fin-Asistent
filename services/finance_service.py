from sqlalchemy.ext.asyncio import AsyncSession

from ai.Context import build_context as _build_context
from db.repos import balance_repo, income_repo, expense_repo, promo_repo


async def build_context(user_id: int, session: AsyncSession) -> dict:
    """
    Собирает context-dict из БД и передаёт в ai.Context.build_context().
    Это главный мост между PostgreSQL и ask_finassist().
    """
    balance = await balance_repo.get(session, user_id)
    current_balance = float(balance.amount) if balance else 0.0

    inc_reg_rows = await income_repo.get_regular(session, user_id)
    inc_irreg_rows = await income_repo.get_all_irregular(session, user_id)

    exp_reg_rows = await expense_repo.get_regular(session, user_id)
    exp_irreg_rows = await expense_repo.get_all_irregular(session, user_id)

    income_reg = [
        {"source": r.source, "amount": float(r.amount), "frequency": r.frequency, "pay_day": r.pay_day}
        for r in inc_reg_rows
    ]
    income_unreg_raw = [
        {"source": r.source, "amount": float(r.amount),
         "received_at": r.received_at.isoformat() if r.received_at else None}
        for r in inc_irreg_rows
    ]
    expenses_reg = [
        {"name": e.name, "amount": float(e.amount), "charge_day": e.charge_day}
        for e in exp_reg_rows
    ]
    expenses_unreg_raw = [
        {"category": e.category, "amount": float(e.amount),
         "is_mandatory": e.is_mandatory,
         "spent_at": e.spent_at.isoformat() if e.spent_at else None}
        for e in exp_irreg_rows
    ]

    promo_rows_orm = await promo_repo.get_active(session)
    promo_rows = [
        {
            "organization": p.organization,
            "purpose": p.purpose,
            "code": p.code,
            "advertiser": p.advertiser or "",
            "erid": p.erid or "",
        }
        for p in promo_rows_orm
    ]

    return _build_context(
        balans=current_balance,
        income_reg=income_reg,
        income_unreg_raw=income_unreg_raw,
        expenses_reg=expenses_reg,
        expenses_unreg_raw=expenses_unreg_raw,
        promo_rows=promo_rows,
    )
