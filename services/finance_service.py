import calendar
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from db.repos import balance_repo, income_repo, expense_repo


async def build_context(user_id: int, session: AsyncSession) -> dict:
    """
    Собирает context-dict из БД для передачи в LLM.
    Это главный мост между PostgreSQL и ai.client.ask_finassist().
    """
    today = date.today()
    month_start = today.replace(day=1)
    month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    # --- Баланс ---
    balance = await balance_repo.get(session, user_id)
    current_balance = float(balance.amount) if balance else 0.0

    # --- Регулярные доходы ---
    income_reg_rows = await income_repo.get_regular(session, user_id)
    income_reg = [
        {
            "source": r.source,
            "amount": float(r.amount),
            "frequency": r.frequency,
            "pay_day": r.pay_day,
        }
        for r in income_reg_rows
    ]

    # --- Нерегулярные доходы за текущий месяц ---
    income_irreg_rows = await income_repo.get_irregular(session, user_id, month_start, month_end)
    income_unreg = [
        {"source": r.source, "amount": float(r.amount)}
        for r in income_irreg_rows
    ]

    # --- Регулярные расходы ---
    expenses_reg_rows = await expense_repo.get_regular(session, user_id)
    expenses_reg = [
        {"name": r.name, "amount": float(r.amount), "charge_day": r.charge_day}
        for r in expenses_reg_rows
    ]

    # --- Нерегулярные расходы за текущий месяц ---
    expenses_irreg_rows = await expense_repo.get_irregular(session, user_id, month_start, month_end)
    expenses_unreg = [
        {
            "category": r.category,
            "amount": float(r.amount),
            "is_mandatory": r.is_mandatory,
        }
        for r in expenses_irreg_rows
    ]

    # --- Расчёт производных балансов ---
    # Регулярные расходы, которые ещё не списались в этом месяце
    upcoming_reg = sum(e["amount"] for e in expenses_reg if e["charge_day"] > today.day)
    balans_after_reg = round(current_balance - upcoming_reg, 2)

    # Все нерегулярные расходы за месяц (уже потраченные)
    unreg_total = sum(e["amount"] for e in expenses_unreg)
    balans_after_unreg = round(balans_after_reg - unreg_total, 2)

    return {
        "balans": current_balance,
        "income_reg": income_reg,
        "income_unreg": income_unreg,
        "expenses_reg": expenses_reg,
        "expenses_unreg": expenses_unreg,
        "income_date": f"{month_start.isoformat()}..{month_end.isoformat()}",
        "balans_after_reg": balans_after_reg,
        "balans_after_unreg": balans_after_unreg,
    }
