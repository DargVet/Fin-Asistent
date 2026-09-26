from sqlalchemy.ext.asyncio import AsyncSession

from db.repos import ai_log_repo
from ai.client import ask_finassist
from services import finance_service

HISTORY_SIZE = 10  # количество последних обменов для контекста

NO_DATA_MSG = (
    "Сначала введи свой баланс и хотя бы один источник дохода — "
    "тогда смогу ответить точно. Используй /setup."
)


async def ask(user_id: int, session: AsyncSession, user_message: str) -> str:
    # Последние N диалогов → история для LLM
    logs = await ai_log_repo.get_last_n(session, user_id, n=HISTORY_SIZE)
    history = []
    for log in logs:
        history.append({"role": "user", "content": log.question})
        if log.answer:
            history.append({"role": "assistant", "content": log.answer})

    # Финансовый контекст из БД
    context = await finance_service.build_context(user_id, session)

    if context["balans"] == 0.0 and not context["income_reg"]:
        return NO_DATA_MSG

    # Вызов LLM с историей
    answer = ask_finassist(user_message, context, history=history)

    # Сохраняем вопрос + ответ для следующих диалогов
    await ai_log_repo.add(session, user_id, user_message, answer=answer)
    await session.commit()

    return answer
