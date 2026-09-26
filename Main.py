from ai.client import ask_finassist

if __name__ == "__main__":
    example_context = {
        "balans": 152300.0,
        "income_reg": [
            {"source": "стипендия", "amount": 5000, "frequency": "monthly", "pay_day": 25},
            {"source": "стипендия", "amount": 9000, "frequency": "monthly", "pay_day": 1}
        ],
        "income_unreg": [{"source": "подработка", "amount": 8000}],
        "expenses_reg": [
            {"name": "аренда", "amount": 8000, "charge_day": 5},
            {"name": "связь", "amount": 500, "charge_day": 10},
        ],
        "expenses_unreg": [
            {"category": "продукты", "amount": 4500, "is_mandatory": True},
            {"category": "кафе", "amount": 2100, "is_mandatory": False},
        ],
        "income_date": "2026-09-01..2026-09-29",
        "balans_after_reg": 6730.0,
        "balans_after_unreg": 10200.0,
    }

    answer = ask_finassist(
        user_message="Могу ли я купить наушники за 4000 рублей?",
        context=example_context,
    )
    print(answer)