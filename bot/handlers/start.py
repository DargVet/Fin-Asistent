from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.menus import main_menu_kb, main_menu_reply_kb
from services import user_service

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    await user_service.get_or_create(session, message.from_user.id)
    # Убираем старую Reply-клавиатуру если она есть
    tmp = await message.answer(".", reply_markup=ReplyKeyboardRemove())
    await tmp.delete()
    await message.answer(
        "Привет! Я финансовый ассистент 💰\n\n"
        "Помогу понять, сколько денег у тебя реально свободно, "
        "хватит ли до следующего дохода и можешь ли ты позволить себе покупку.\n\n"
        "Выбери раздел или просто напиши свой вопрос:",
        reply_markup=main_menu_kb(),
    )
