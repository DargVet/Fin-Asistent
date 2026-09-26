from datetime import date
from typing import Optional

from .finance import (
    filter_current_month,
    compute_month_balances,
    get_next_income_info,
    get_next_expense_info,
)


def build_promo_codes_dict(promo_rows: list) -> dict:
    """Собирает промокоды из плоских строк таблицы promo_codes в вид
    {organization: {purpose: code}}.
    Ожидает список dict с ключами: organization, purpose, code."""
    promo_codes: dict = {}
    for row in promo_rows:
        org = row["organization"]
        purpose = row["purpose"]
        code = row["code"]
        promo_codes.setdefault(org, {})[purpose] = code
    return promo_codes


def build_context(
    balans: float,
    income_reg: list,
    income_unreg_raw: list,
    expenses_reg: list,
    expenses_unreg_raw: list,
    promo_rows: Optional[list] = None,
    today: Optional[date] = None,
) -> dict:
    """
    Собирает единый context для ask_finassist из "сырых" данных БД.
    Вызывать один раз перед ask_finassist (например, в обработчике сообщения бота).

    balans             — balances.amount пользователя
    income_reg         — строки income_regular (source, amount, frequency, pay_day)
    income_unreg_raw   — строки income_irregular (source, amount, received_at) за
                          ЛЮБОЙ период — функция сама отфильтрует текущий месяц
    expenses_reg       — строки expenses_regular (name, amount, charge_day)
    expenses_unreg_raw — строки expenses_irregular (category, amount, is_mandatory,
                          spent_at) за любой период — тоже фильтруется по месяцу
    promo_rows         — строки таблицы promo_codes (organization, purpose, code);
                          можно не передавать, если промокодов пока нет
    """
    today = today or date.today()
    promo_rows = promo_rows or []

    income_unreg = filter_current_month(income_unreg_raw, "received_at", today)
    expenses_unreg = filter_current_month(expenses_unreg_raw, "spent_at", today)

    balances = compute_month_balances(balans, expenses_reg, expenses_unreg, today)
    next_income = get_next_income_info(income_reg, today)
    next_expense = get_next_expense_info(expenses_reg, today)

    income_before_next_expense = None
    if next_income["next_income_date"] and next_expense["next_expense_date"]:
        income_before_next_expense = next_income["next_income_date"] < next_expense["next_expense_date"]

    return {
        "today_date": today.isoformat(),
        "balans": balans,
        "income_reg": income_reg,
        "income_unreg": income_unreg,
        "expenses_reg": expenses_reg,
        "expenses_unreg": expenses_unreg,
        "promo_codes": build_promo_codes_dict(promo_rows),
        **balances,
        **next_income,
        **next_expense,
        # True  — доход придёт раньше, чем спишется ближайший обязательный платёж
        #         (можно мягко намекнуть, что есть немного свободы для покупки)
        # False — обязательный платёж наступит раньше дохода (лучше придержать деньги)
        # None  — не хватает данных, чтобы сравнить (нет ни дохода, ни платежа)
        "income_before_next_expense": income_before_next_expense,
    }