from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.menus import main_menu_kb

router = Router()


@router.callback_query(F.data == "mm")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("🏠 ГЛАВНОЕ МЕНЮ\n\nВыбери раздел:", reply_markup=main_menu_kb())
    await callback.answer()


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("🏠 ГЛАВНОЕ МЕНЮ\n\nВыбери раздел:", reply_markup=main_menu_kb())
