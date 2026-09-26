import json

from groq import Groq

from .config import GROQ_API_KEY, MODEL_NAME
from .guardrails import check_guardrails
from .finance import check_purchase_affordability
from .tools import TOOLS
from .prompts import build_system_prompt

client = Groq(api_key=GROQ_API_KEY)


def ask_finassist(user_message: str, context: dict) -> str:
    """
    context должен быть УЖЕ полностью собран через context.build_context(...)
    до вызова этой функции (обычно — в обработчике сообщения бота, сразу после
    того как достал свежие данные пользователя из БД). Здесь context больше
    ничего не досчитывает и не дополняет — только передаёт модели как есть.

    Ожидаемые ключи (их формирует build_context):
        today_date, balans,
        income_reg, income_unreg (уже отфильтрован по текущему месяцу),
        expenses_reg, expenses_unreg (уже отфильтрован по текущему месяцу),
        promo_codes,
        reserved_for_month, reserved_for_month_items,
        balans_after_reg, unreg_total, balans_after_unreg,
        next_income_date, next_income_source, next_income_amount, days_until_income,
        next_expense_date, next_expense_name, next_expense_amount, days_until_expense,
        income_before_next_expense
    """
    refusal = check_guardrails(user_message)
    if refusal:
        return refusal

    messages = [
        {"role": "system", "content": build_system_prompt(context)},
        {"role": "user", "content": user_message},
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=500,
            timeout=10,
        )
        message = response.choices[0].message

        if message.tool_calls:
            messages.append(message)
            for tool_call in message.tool_calls:
                if tool_call.function.name == "check_purchase_affordability":
                    args = json.loads(tool_call.function.arguments)
                    result = check_purchase_affordability(args["amount"], context)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )

            final_response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
                timeout=10,
            )
            return final_response.choices[0].message.content

        return message.content

    except Exception as exc:  # noqa: BLE001 — хакатон, ловим широко для fallback
        print(f"[finassist.client] API error: {exc}")
        return (
            "Сейчас не получается обработать запрос — попробуй ещё раз "
            "через минуту."
        )