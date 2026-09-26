from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main_kb import main_keyboard
from services import user_service

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    await user_service.get_or_create(session, message.from_user.id)
    await message.answer(
        "Привет! Я финансовый ассистент 💰\n\n"
        "Помогу понять, сколько денег у тебя реально свободно, "
        "хватит ли до следующего дохода и можешь ли ты позволить себе покупку.\n\n"
        "Для начала настрой свои данные — нажми «⚙️ Настроить данные» "
        "или отправь /setup.",
        reply_markup=main_keyboard,
    )
