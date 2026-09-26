import calendar
from datetime import date


def get_next_income_info(income_reg: list, today: date) -> dict:
    """Ищет ближайшую дату дохода среди всех регулярных поступлений
    (у каждого item должен быть pay_day — число месяца)."""
    candidates = []
    for item in income_reg:
        pay_day = item.get("pay_day")
        if pay_day is None:
            continue

        last_day_this_month = calendar.monthrange(today.year, today.month)[1]
        candidate = today.replace(day=min(pay_day, last_day_this_month))

        if candidate <= today:
            next_month = today.month % 12 + 1
            next_year = today.year + (1 if today.month == 12 else 0)
            last_day_next_month = calendar.monthrange(next_year, next_month)[1]
            candidate = date(next_year, next_month, min(pay_day, last_day_next_month))

        candidates.append((candidate, item.get("source", "доход")))

    if not candidates:
        return {"next_income_date": None, "next_income_source": None, "days_until_income": None}

    candidates.sort(key=lambda pair: pair[0])
    next_date, source = candidates[0]
    return {
        "next_income_date": next_date.isoformat(),
        "next_income_source": source,
        "days_until_income": (next_date - today).days,
    }


def check_purchase_affordability(amount: float, context: dict) -> dict:
    """balans_after_unreg уже учитывает и обязательные, и необязательные
    траты до конца месяца — поэтому достаточно просто вычесть amount."""
    balans_after_unreg = context["balans_after_unreg"]
    after_purchase = balans_after_unreg - amount

    return {
        "can_afford": after_purchase >= 0,
        "balans_after_unreg_before_purchase": balans_after_unreg,
        "balans_after_purchase": round(after_purchase, 2),
    }