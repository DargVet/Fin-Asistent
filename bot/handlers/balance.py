from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.menus import main_menu_kb, prompt_kb
from db.repos import balance_repo
from services import user_service

router = Router()


class BalanceStates(StatesGroup):
    waiting = State()


@router.callback_query(F.data == "bal")
async def cb_balance(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    user = await user_service.get_or_create(session, callback.from_user.id)
    balance = await balance_repo.get(session, user.id)
    current = f"{float(balance.amount):,.0f} ₽" if balance else "не задан"
    await state.set_state(BalanceStates.waiting)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.message.edit_text(
        f"🔄 ОБНОВИТЬ БАЛАНС\n\nТекущий баланс: {current}\n\nВведи новую сумму (₽):",
        reply_markup=prompt_kb("mm"),
    )
    await callback.answer()


@router.message(BalanceStates.waiting)
async def process_balance(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.delete()
        return
    data = await state.get_data()
    user = await user_service.get_or_create(session, message.from_user.id)
    await balance_repo.upsert(session, user.id, amount)
    await session.commit()
    await state.clear()
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text=f"✓ Баланс обновлён: {amount:,.0f} ₽\n\nВыбери раздел:",
        reply_markup=main_menu_kb(),
    )
    await message.delete()
