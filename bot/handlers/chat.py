from aiogram import Router, F
from aiogram.fsm.state import default_state
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from services import ai_service, user_service, finance_service

router = Router()


@router.message(F.text == "📊 Моя ситуация")
async def cmd_situation(message: Message, session: AsyncSession) -> None:
    """Показывает краткую финансовую сводку без вызова LLM."""
    user = await user_service.get_or_create(session, message.from_user.id)
    ctx = await finance_service.build_context(user.id, session)

    if ctx["balans"] == 0.0 and not ctx["income_reg"]:
        await message.answer("Данных пока нет. Пройди настройку: /setup")
        return

    reg_names = ", ".join(e["name"] for e in ctx["expenses_reg"]) or "нет"
    await message.answer(
        f"💰 Баланс: {ctx['balans']:,.0f} ₽\n"
        f"📤 После обязательных платежей: {ctx['balans_after_reg']:,.0f} ₽\n"
        f"🆓 Свободно (с учётом трат): {ctx['balans_after_unreg']:,.0f} ₽\n\n"
        f"Регулярные расходы: {reg_names}"
    )


@router.message(F.text == "💬 Спросить ассистента")
async def cmd_ask_hint(message: Message) -> None:
    await message.answer("Просто напиши свой вопрос, например:\n«Могу ли я купить наушники за 4000 ₽?»")


@router.message(default_state, F.text)
async def handle_chat(message: Message, session: AsyncSession) -> None:
    """Ловит все текстовые сообщения вне FSM и отправляет в LLM."""
    user = await user_service.get_or_create(session, message.from_user.id)

    await message.bot.send_chat_action(message.chat.id, "typing")

    answer = await ai_service.ask(
        user_id=user.id,
        session=session,
        user_message=message.text,
    )
    await message.answer(answer)
