from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.menus import (
    income_menu_kb, income_regular_kb, income_item_kb,
    income_irregular_kb, prompt_kb, back_only_kb,
)
from db.repos import income_repo, balance_repo, expense_repo
from services import user_service

router = Router()


class IncomeStates(StatesGroup):
    update_amount = State()   # data: income_id, msg_id
    new_name      = State()   # data: msg_id
    new_amount    = State()   # data: msg_id, new_name
    new_pay_day   = State()   # data: msg_id, new_name, new_amount
    irregular     = State()   # data: msg_id  («Название Сумма»)


# ── Меню доходов ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "inc_m")
async def cb_income_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("💰 ДОХОДЫ\n\nВыбери тип:", reply_markup=income_menu_kb())
    await callback.answer()


# ── Постоянные доходы ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "inc_r")
async def cb_income_regular(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    user = await user_service.get_or_create(session, callback.from_user.id)
    items = await income_repo.get_regular(session, user.id)
    text = "📌 ПОСТОЯННЫЕ ДОХОДЫ\n\nВыбери категорию или добавь новую:"
    if not items:
        text = "📌 ПОСТОЯННЫЕ ДОХОДЫ\n\nКатегорий пока нет. Добавь первую:"
    await callback.message.edit_text(text, reply_markup=income_regular_kb(items))
    await callback.answer()


@router.callback_query(F.data.startswith("inc_sel_"))
async def cb_income_select(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    income_id = int(callback.data.split("_")[-1])
    item = await session.get(__import__("db.models", fromlist=["IncomeRegular"]).IncomeRegular, income_id)
    if not item:
        await callback.answer("Не найдено")
        return
    await callback.message.edit_text(
        f"📌 {item.source}\n\nСумма: {float(item.amount):,.0f} ₽\nДень выплаты: {item.pay_day}-е число",
        reply_markup=income_item_kb(income_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("inc_upd_"))
async def cb_income_update(callback: CallbackQuery, state: FSMContext) -> None:
    income_id = int(callback.data.split("_")[-1])
    await state.set_state(IncomeStates.update_amount)
    await state.update_data(income_id=income_id, msg_id=callback.message.message_id)
    await callback.message.edit_text(
        "Введи новую сумму (₽):",
        reply_markup=prompt_kb("inc_r"),
    )
    await callback.answer()


@router.message(IncomeStates.update_amount)
async def process_income_update(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.delete()
        return
    data = await state.get_data()
    await income_repo.update_regular_amount(session, data["income_id"], amount)
    await session.commit()
    await state.clear()
    user = await user_service.get_or_create(session, message.from_user.id)
    items = await income_repo.get_regular(session, user.id)
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text="📌 ПОСТОЯННЫЕ ДОХОДЫ\n\nСумма обновлена ✓",
        reply_markup=income_regular_kb(items),
    )
    await message.delete()


@router.callback_query(F.data.startswith("inc_del_"))
async def cb_income_delete(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    income_id = int(callback.data.split("_")[-1])
    item = await session.get(__import__("db.models", fromlist=["IncomeRegular"]).IncomeRegular, income_id)
    deleted_amount = float(item.amount) if item else 0.0
    deleted_name = item.source if item else "доход"

    await income_repo.delete_regular(session, income_id)

    # Обновляем баланс
    user = await user_service.get_or_create(session, callback.from_user.id)
    balance = await balance_repo.get(session, user.id)
    if balance:
        await balance_repo.upsert(session, user.id, float(balance.amount) - deleted_amount)

    # Записываем в историю
    await expense_repo.add_irregular(
        session, user.id,
        category=f"Удалён регулярный доход: {deleted_name}",
        amount=deleted_amount,
        is_mandatory=False,
    )

    await session.commit()
    items = await income_repo.get_regular(session, user.id)
    await callback.message.edit_text(
        "📌 ПОСТОЯННЫЕ ДОХОДЫ\n\nКатегория удалена ✓",
        reply_markup=income_regular_kb(items),
    )
    await callback.answer()


# ── Новая категория постоянного дохода ───────────────────────────────────────

@router.callback_query(F.data == "inc_new")
async def cb_income_new(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(IncomeStates.new_name)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.message.edit_text(
        "Введи название источника дохода:\n(например: стипендия, подработка)",
        reply_markup=prompt_kb("inc_r"),
    )
    await callback.answer()


@router.message(IncomeStates.new_name)
async def process_income_new_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(new_name=message.text.strip())
    await state.set_state(IncomeStates.new_amount)
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text=f"Сумма для «{message.text.strip()}» (₽):",
        reply_markup=prompt_kb("inc_r"),
    )
    await message.delete()


@router.message(IncomeStates.new_amount)
async def process_income_new_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.delete()
        return
    data = await state.get_data()
    await state.update_data(new_amount=amount)
    await state.set_state(IncomeStates.new_pay_day)
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text="В какой день месяца приходит? (1–31):",
        reply_markup=prompt_kb("inc_r"),
    )
    await message.delete()


@router.message(IncomeStates.new_pay_day)
async def process_income_new_day(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        day = int(message.text.strip())
        if not 1 <= day <= 31:
            raise ValueError
    except ValueError:
        await message.delete()
        return
    data = await state.get_data()
    user = await user_service.get_or_create(session, message.from_user.id)
    await income_repo.add_regular(session, user.id, data["new_name"], data["new_amount"], day)

    # Обновляем баланс
    balance = await balance_repo.get(session, user.id)
    if balance:
        await balance_repo.upsert(session, user.id, float(balance.amount) + data["new_amount"])

    # Записываем в историю
    await expense_repo.add_irregular(
        session, user.id,
        category=f"Добавлен регулярный доход: {data['new_name']}",
        amount=data["new_amount"],
        is_mandatory=False,
    )

    await session.commit()
    await state.clear()
    items = await income_repo.get_regular(session, user.id)
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text=f"📌 ПОСТОЯННЫЕ ДОХОДЫ\n\n«{data['new_name']}» добавлен ✓",
        reply_markup=income_regular_kb(items),
    )
    await message.delete()


# ── Разовые доходы ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "inc_i")
async def cb_income_irregular(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "⚡️ РАЗОВЫЕ ДОХОДЫ\n\nНажми «Добавить» и введи одной строкой:\nНазвание Сумма\n\nПример: подработка 3000",
        reply_markup=income_irregular_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "inc_i_add")
async def cb_income_irregular_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(IncomeStates.irregular)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.message.edit_text(
        "Введи одной строкой:\nНазвание Сумма\n\nПример: подработка 3000",
        reply_markup=prompt_kb("inc_i"),
    )
    await callback.answer()


@router.message(IncomeStates.irregular)
async def process_income_irregular(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        parts = message.text.rsplit(" ", 1)
        source = parts[0].strip()
        amount = float(parts[1].replace(",", "."))
    except (ValueError, IndexError):
        await message.delete()
        return
    data = await state.get_data()
    user = await user_service.get_or_create(session, message.from_user.id)
    await income_repo.add_irregular(session, user.id, source, amount)
    balance = await balance_repo.get(session, user.id)
    if balance:
        await balance_repo.upsert(session, user.id, float(balance.amount) + amount)
    await session.commit()
    await state.clear()
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text=f"⚡️ РАЗОВЫЕ ДОХОДЫ\n\n«{source}» {amount:,.0f} ₽ добавлен ✓",
        reply_markup=income_irregular_kb(),
    )
    await message.delete()
