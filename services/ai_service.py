from sqlalchemy.ext.asyncio import AsyncSession

from core.config import FREE_PLAN_DAILY_LIMIT
from db.repos import user_repo, ai_log_repo
from ai.client import ask_finassist
from services import finance_service

LIMIT_EXCEEDED_MSG = (
    "Ты достиг дневного лимита запросов ({limit}) на бесплатном тарифе. "
    "Обнови план до Premium, чтобы задавать вопросы без ограничений."
).format(limit=FREE_PLAN_DAILY_LIMIT)

NO_DATA_MSG = (
    "Сначала введи свой баланс и хотя бы один источник дохода — "
    "тогда смогу ответить точно. Используй /setup."
)


async def ask(user_id: int, session: AsyncSession, user_message: str) -> str:
    # Проверка лимита для free-тарифа
    user = await user_repo.get_by_id(session, user_id)
    if user and user.plan == "free":
        today_count = await ai_log_repo.count_today(session, user_id)
        if today_count >= FREE_PLAN_DAILY_LIMIT:
            return LIMIT_EXCEEDED_MSG

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
