from aiogram import Router, F
from aiogram.fsm.state import default_state
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from services import ai_service, user_service

router = Router()


@router.message(default_state, F.text)
async def handle_chat(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(session, message.from_user.id)
    await message.bot.send_chat_action(message.chat.id, "typing")
    answer = await ai_service.ask(user_id=user.id, session=session, user_message=message.text)
    await message.answer(answer)
