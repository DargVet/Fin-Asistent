from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.menus import (
    expense_menu_kb, expense_regular_kb, expense_item_kb,
    expense_irregular_kb, prompt_kb,
)
from db.repos import expense_repo, balance_repo
from services import user_service

router = Router()


class ExpenseStates(StatesGroup):
    update_amount  = State()
    new_name       = State()
    new_amount     = State()
    new_charge_day = State()
    irregular      = State()


# ── Меню расходов ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "exp_m")
async def cb_expense_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("💸 РАСХОДЫ\n\nВыбери тип:", reply_markup=expense_menu_kb())
    await callback.answer()


# ── Постоянные расходы ────────────────────────────────────────────────────────

@router.callback_query(F.data == "exp_r")
async def cb_expense_regular(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    user = await user_service.get_or_create(session, callback.from_user.id)
    items = await expense_repo.get_regular(session, user.id)
    text = "📌 ПОСТОЯННЫЕ РАСХОДЫ\n\nВыбери категорию или добавь новую:"
    if not items:
        text = "📌 ПОСТОЯННЫЕ РАСХОДЫ\n\nКатегорий пока нет. Добавь первую:"
    await callback.message.edit_text(text, reply_markup=expense_regular_kb(items))
    await callback.answer()


@router.callback_query(F.data.startswith("exp_sel_"))
async def cb_expense_select(callback: CallbackQuery, session: AsyncSession) -> None:
    expense_id = int(callback.data.split("_")[-1])
    from db.models import ExpenseRegular
    item = await session.get(ExpenseRegular, expense_id)
    if not item:
        await callback.answer("Не найдено")
        return
    await callback.message.edit_text(
        f"📌 {item.name}\n\nСумма: {float(item.amount):,.0f} ₽\nДень списания: {item.charge_day}-е число",
        reply_markup=expense_item_kb(expense_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("exp_upd_"))
async def cb_expense_update(callback: CallbackQuery, state: FSMContext) -> None:
    expense_id = int(callback.data.split("_")[-1])
    await state.set_state(ExpenseStates.update_amount)
    await state.update_data(expense_id=expense_id, msg_id=callback.message.message_id)
    await callback.message.edit_text("Введи новую сумму (₽):", reply_markup=prompt_kb("exp_r"))
    await callback.answer()


@router.message(ExpenseStates.update_amount)
async def process_expense_update(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.delete()
        return
    data = await state.get_data()
    await expense_repo.update_regular_amount(session, data["expense_id"], amount)
    await session.commit()
    await state.clear()
    user = await user_service.get_or_create(session, message.from_user.id)
    items = await expense_repo.get_regular(session, user.id)
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text="📌 ПОСТОЯННЫЕ РАСХОДЫ\n\nСумма обновлена ✓",
        reply_markup=expense_regular_kb(items),
    )
    await message.delete()


@router.callback_query(F.data.startswith("exp_del_"))
async def cb_expense_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    expense_id = int(callback.data.split("_")[-1])
    await expense_repo.delete_regular(session, expense_id)
    await session.commit()
    user = await user_service.get_or_create(session, callback.from_user.id)
    items = await expense_repo.get_regular(session, user.id)
    await callback.message.edit_text(
        "📌 ПОСТОЯННЫЕ РАСХОДЫ\n\nКатегория удалена ✓",
        reply_markup=expense_regular_kb(items),
    )
    await callback.answer()


# ── Новая категория постоянного расхода ──────────────────────────────────────

@router.callback_query(F.data == "exp_new")
async def cb_expense_new(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ExpenseStates.new_name)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.message.edit_text(
        "Введи название расхода:\n(например: аренда, связь, подписки)",
        reply_markup=prompt_kb("exp_r"),
    )
    await callback.answer()


@router.message(ExpenseStates.new_name)
async def process_expense_new_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(new_name=message.text.strip())
    await state.set_state(ExpenseStates.new_amount)
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text=f"Сумма для «{message.text.strip()}» (₽):",
        reply_markup=prompt_kb("exp_r"),
    )
    await message.delete()


@router.message(ExpenseStates.new_amount)
async def process_expense_new_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.delete()
        return
    data = await state.get_data()
    await state.update_data(new_amount=amount)
    await state.set_state(ExpenseStates.new_charge_day)
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text="В какой день месяца списывается? (1–31):",
        reply_markup=prompt_kb("exp_r"),
    )
    await message.delete()


@router.message(ExpenseStates.new_charge_day)
async def process_expense_new_day(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        day = int(message.text.strip())
        if not 1 <= day <= 31:
            raise ValueError
    except ValueError:
        await message.delete()
        return
    data = await state.get_data()
    user = await user_service.get_or_create(session, message.from_user.id)
    await expense_repo.add_regular(session, user.id, data["new_name"], data["new_amount"], day)
    await session.commit()
    await state.clear()
    items = await expense_repo.get_regular(session, user.id)
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text=f"📌 ПОСТОЯННЫЕ РАСХОДЫ\n\n«{data['new_name']}» добавлен ✓",
        reply_markup=expense_regular_kb(items),
    )
    await message.delete()


# ── Разовые расходы ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "exp_i")
async def cb_expense_irregular(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "⚡️ РАЗОВЫЕ РАСХОДЫ\n\nНажми «Добавить» и введи одной строкой:\nНазвание Сумма\n\nПример: продукты 1500",
        reply_markup=expense_irregular_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "exp_i_add")
async def cb_expense_irregular_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ExpenseStates.irregular)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.message.edit_text(
        "Введи одной строкой:\nНазвание Сумма\n\nПример: продукты 1500",
        reply_markup=prompt_kb("exp_i"),
    )
    await callback.answer()


@router.message(ExpenseStates.irregular)
async def process_expense_irregular(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        parts = message.text.rsplit(" ", 1)
        category = parts[0].strip()
        amount = float(parts[1].replace(",", "."))
    except (ValueError, IndexError):
        await message.delete()
        return
    data = await state.get_data()
    user = await user_service.get_or_create(session, message.from_user.id)
    await expense_repo.add_irregular(session, user.id, category, amount)
    balance = await balance_repo.get(session, user.id)
    if balance:
        await balance_repo.upsert(session, user.id, float(balance.amount) - amount)
    await session.commit()
    await state.clear()
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text=f"⚡️ РАЗОВЫЕ РАСХОДЫ\n\n«{category}» {amount:,.0f} ₽ добавлен ✓",
        reply_markup=expense_irregular_kb(),
    )
    await message.delete()
