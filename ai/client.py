import json
from datetime import date

from groq import Groq

from core.config import GROQ_API_KEY, MODEL_NAME
from .guardrails import check_guardrails
from .finance import get_next_income_info, check_purchase_affordability
from .tools import TOOLS
from .prompts import build_system_prompt

client = Groq(api_key=GROQ_API_KEY)


def ask_finassist(user_message: str, context: dict) -> str:
    """
    context — dict с ключами:
        balans, income_reg (каждый item может содержать pay_day),
        income_unreg, expenses_reg, expenses_unreg,
        income_date, balans_after_reg, balans_after_unreg
    today_date / next_income_date / next_income_source / days_until_income
    досчитываются здесь автоматически — их передавать не нужно.
    """
    refusal = check_guardrails(user_message)
    if refusal:
        return refusal

    today = date.today()
    context = {
        **context,
        "today_date": today.isoformat(),
        **get_next_income_info(context.get("income_reg", []), today),
    }

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
