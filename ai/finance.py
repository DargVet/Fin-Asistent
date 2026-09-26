import calendar
from datetime import date, datetime


def _to_date(value) -> date:
    """Приводит значение из БД (datetime/date/строка) к date для сравнений."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)).date()


def filter_current_month(items: list, date_field: str, today: date) -> list:
    """Оставляет только записи, чья дата попадает в текущий месяц/год.
    Используется для income_irregular (received_at) и expenses_irregular (spent_at) —
    в БД они хранятся за всё время, а в контекст ИИ должны попадать только за месяц."""
    result = []
    for item in items:
        item_date = _to_date(item[date_field])
        if item_date.year == today.year and item_date.month == today.month:
            result.append(item)
    return result


def _next_occurrence(day_of_month: int, today: date) -> date:
    """Ближайшая дата в этом или следующем месяце, когда наступает day_of_month.
    Если день в этом месяце уже прошёл (или наступает сегодня) — берём следующий месяц."""
    last_day_this_month = calendar.monthrange(today.year, today.month)[1]
    candidate = today.replace(day=min(day_of_month, last_day_this_month))

    if candidate <= today:
        next_month = today.month % 12 + 1
        next_year = today.year + (1 if today.month == 12 else 0)
        last_day_next_month = calendar.monthrange(next_year, next_month)[1]
        candidate = date(next_year, next_month, min(day_of_month, last_day_next_month))

    return candidate


def get_next_income_info(income_reg: list, today: date) -> dict:
    """Ищет ближайшую дату дохода среди всех регулярных поступлений
    (у каждого item должен быть pay_day — число месяца)."""
    candidates = []
    for item in income_reg:
        pay_day = item.get("pay_day")
        if pay_day is None:
            continue
        candidates.append(
            (_next_occurrence(pay_day, today), item.get("source", "доход"), item.get("amount"))
        )

    if not candidates:
        return {
            "next_income_date": None,
            "next_income_source": None,
            "next_income_amount": None,
            "days_until_income": None,
        }

    candidates.sort(key=lambda triple: triple[0])
    next_date, source, amount = candidates[0]
    return {
        "next_income_date": next_date.isoformat(),
        "next_income_source": source,
        "next_income_amount": amount,
        "days_until_income": (next_date - today).days,
    }


def get_next_expense_info(expenses_reg: list, today: date) -> dict:
    """Ищет ближайшую дату регулярного расхода (по charge_day)."""
    candidates = []
    for item in expenses_reg:
        charge_day = item.get("charge_day")
        if charge_day is None:
            continue

        last_day_this_month = calendar.monthrange(today.year, today.month)[1]
        candidate = today.replace(day=min(charge_day, last_day_this_month))

        if candidate <= today:
            next_month = today.month % 12 + 1
            next_year = today.year + (1 if today.month == 12 else 0)
            last_day_next_month = calendar.monthrange(next_year, next_month)[1]
            candidate = date(next_year, next_month, min(charge_day, last_day_next_month))

        candidates.append((candidate, item.get("name", "расход"), item.get("amount", 0)))

    if not candidates:
        return {"next_expense_date": None, "next_expense_name": None,
                "next_expense_amount": None, "days_until_expense": None}

    candidates.sort(key=lambda x: x[0])
    next_date, name, amount = candidates[0]
    return {
        "next_expense_date": next_date.isoformat(),
        "next_expense_name": name,
        "next_expense_amount": amount,
        "days_until_expense": (next_date - today).days,
    }


def check_purchase_affordability(amount: float, context: dict) -> dict:
    """balans_after_unreg уже учитывает и обязательные регулярные, и уже
    потраченные нерегулярные траты — поэтому достаточно просто вычесть amount.
    Расчёт намеренно консервативный: не учитывает будущие доходы, даже если
    они наступят раньше следующего обязательного платежа (см. context.py)."""
    balans_after_unreg = context["balans_after_unreg"]
    after_purchase = balans_after_unreg - amount

    return {
        "can_afford": after_purchase >= 0,
        "balans_after_unreg_before_purchase": balans_after_unreg,
        "balans_after_purchase": round(after_purchase, 2),
    }