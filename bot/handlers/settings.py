from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.menus import settings_menu_kb, confirm_clear_kb, main_menu_kb
from services import user_service

router = Router()


@router.callback_query(F.data == "set_m")
async def cb_settings(callback: CallbackQuery) -> None:
    await callback.message.edit_text("⚙️ НАСТРОЙКИ", reply_markup=settings_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "set_clr")
async def cb_settings_clear(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Удалить все данные?\n\nБаланс, доходы, расходы и цели будут стёрты. Аккаунт сохранится.",
        reply_markup=confirm_clear_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "set_clr_ok")
async def cb_settings_clear_ok(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await user_service.get_or_create(session, callback.from_user.id)
    await user_service.clear_all_data(session, user.id)
    await callback.message.edit_text(
        "✓ Все данные удалены.\n\nВыбери раздел:",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()
