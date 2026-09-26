from sqlalchemy.ext.asyncio import AsyncSession

from db.repos import ai_log_repo
from ai.client import ask_finassist
from services import finance_service

NO_DATA_MSG = (
    "Сначала введи свой баланс и хотя бы один источник дохода — "
    "тогда смогу ответить точно. Используй /setup."
)


async def ask(user_id: int, session: AsyncSession, user_message: str) -> str:
    # Собираем контекст из БД
    context = await finance_service.build_context(user_id, session)

    # Если данных ещё нет — просим пройти онбординг
    if context["balans"] == 0.0 and not context["income_reg"]:
        return NO_DATA_MSG

    # Вызов LLM
    answer = ask_finassist(user_message, context)

    # Логируем запрос
    await ai_log_repo.add(session, user_id, user_message)
    await session.commit()

    return answer
