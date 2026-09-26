from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from db.repos import balance_repo, income_repo, expense_repo
from services import user_service

router = Router()


class SetupStates(StatesGroup):
    balance = State()
    income_source = State()
    income_amount = State()
    income_day = State()
    expense_name = State()
    expense_amount = State()
    expense_day = State()


def _continue_income_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить ещё доход", callback_data="add_income")],
        [InlineKeyboardButton(text="➡️ Перейти к расходам", callback_data="to_expenses")],
    ])


def _continue_expense_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить ещё расход", callback_data="add_expense")],
        [InlineKeyboardButton(text="✅ Готово", callback_data="setup_done")],
    ])


# ── Старт настройки ──────────────────────────────────────────────────────────

@router.message(Command("setup"))
@router.message(F.text == "⚙️ Настроить данные")
async def cmd_setup(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await user_service.get_or_create(session, message.from_user.id)
    await state.set_state(SetupStates.balance)
    await message.answer("Шаг 1/3 — Введи текущий баланс в рублях (только число):\n\nПример: 24500")


# ── Баланс ───────────────────────────────────────────────────────────────────

@router.message(SetupStates.balance)
async def process_balance(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.answer("Не понял число. Введи сумму цифрами, например: 24500")
        return

    user = await user_service.get_or_create(session, message.from_user.id)
    await balance_repo.upsert(session, user.id, amount)
    await session.commit()

    await state.set_state(SetupStates.income_source)
    await message.answer(
        f"Баланс {amount:,.0f} ₽ сохранён ✓\n\n"
        "Шаг 2/3 — Добавим регулярные доходы.\n"
        "Как называется источник? (например: стипендия, зарплата, подработка)"
    )


# ── Регулярный доход ─────────────────────────────────────────────────────────

@router.message(SetupStates.income_source)
async def process_income_source(message: Message, state: FSMContext) -> None:
    await state.update_data(income_source=message.text.strip())
    await state.set_state(SetupStates.income_amount)
    await message.answer("Сумма в рублях:")


@router.message(SetupStates.income_amount)
async def process_income_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.answer("Введи сумму цифрами, например: 9000")
        return

    await state.update_data(income_amount=amount)
    await state.set_state(SetupStates.income_day)
    await message.answer("В какой день месяца приходит? Введи число от 1 до 31:")


@router.message(SetupStates.income_day)
async def process_income_day(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        day = int(message.text.strip())
        if not 1 <= day <= 31:
            raise ValueError
    except ValueError:
        await message.answer("Введи число от 1 до 31:")
        return

    data = await state.get_data()
    user = await user_service.get_or_create(session, message.from_user.id)
    await income_repo.add_regular(
        session,
        user_id=user.id,
        source=data["income_source"],
        amount=data["income_amount"],
        pay_day=day,
    )
    await session.commit()

    await state.set_state(SetupStates.income_source)
    await message.answer(
        f"Доход «{data['income_source']}» {data['income_amount']:,.0f} ₽ (день {day}) сохранён ✓",
        reply_markup=_continue_income_kb(),
    )


@router.callback_query(F.data == "add_income")
async def cb_add_income(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SetupStates.income_source)
    await callback.message.answer("Название следующего источника дохода:")
    await callback.answer()


@router.callback_query(F.data == "to_expenses")
async def cb_to_expenses(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SetupStates.expense_name)
    await callback.message.answer(
        "Шаг 3/3 — Добавим регулярные расходы.\n"
        "Как называется? (например: аренда, связь, подписки)"
    )
    await callback.answer()


# ── Регулярный расход ─────────────────────────────────────────────────────────

@router.message(SetupStates.expense_name)
async def process_expense_name(message: Message, state: FSMContext) -> None:
    await state.update_data(expense_name=message.text.strip())
    await state.set_state(SetupStates.expense_amount)
    await message.answer("Сумма в рублях:")


@router.message(SetupStates.expense_amount)
async def process_expense_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.answer("Введи сумму цифрами, например: 8000")
        return

    await state.update_data(expense_amount=amount)
    await state.set_state(SetupStates.expense_day)
    await message.answer("В какой день месяца списывается? Введи число от 1 до 31:")


@router.message(SetupStates.expense_day)
async def process_expense_day(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        day = int(message.text.strip())
        if not 1 <= day <= 31:
            raise ValueError
    except ValueError:
        await message.answer("Введи число от 1 до 31:")
        return

    data = await state.get_data()
    user = await user_service.get_or_create(session, message.from_user.id)
    await expense_repo.add_regular(
        session,
        user_id=user.id,
        name=data["expense_name"],
        amount=data["expense_amount"],
        charge_day=day,
    )
    await session.commit()

    await state.set_state(SetupStates.expense_name)
    await message.answer(
        f"Расход «{data['expense_name']}» {data['expense_amount']:,.0f} ₽ (день {day}) сохранён ✓",
        reply_markup=_continue_expense_kb(),
    )


@router.callback_query(F.data == "add_expense")
async def cb_add_expense(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SetupStates.expense_name)
    await callback.message.answer("Название следующего расхода:")
    await callback.answer()


@router.callback_query(F.data == "setup_done")
async def cb_setup_done(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        "Всё настроено! 🎉\n\n"
        "Теперь просто пиши мне вопросы:\n"
        "• «Могу ли я потратить 3000 ₽?»\n"
        "• «Хватит ли денег до конца месяца?»\n"
        "• «Куда уходят деньги?»"
    )
    await callback.answer()
