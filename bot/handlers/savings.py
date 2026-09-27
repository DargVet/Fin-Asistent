from datetime import date

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.menus import (
    savings_menu_kb, goals_list_kb, confirm_delete_goal_kb, prompt_kb,
)
from db.repos import goal_repo, balance_repo, expense_repo, income_repo
from services import user_service

router = Router()


class SavingsStates(StatesGroup):
    goal_name    = State()
    goal_amount  = State()
    goal_deadline = State()
    add_amount   = State()   # data: goal_id


@router.callback_query(F.data == "sav_m")
async def cb_savings_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("🏦 НАКОПИТЬ\n\nВыбери действие:", reply_markup=savings_menu_kb())
    await callback.answer()


# ── Посмотреть цели ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "sav_view")
async def cb_savings_view(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await user_service.get_or_create(session, callback.from_user.id)
    goals = await goal_repo.get_all(session, user.id)
    if not goals:
        await callback.message.edit_text("Целей пока нет.", reply_markup=savings_menu_kb())
        await callback.answer()
        return
    lines = ["📊 НАКОПЛЕНИЯ\n"]
    for g in goals:
        pct = float(g.current_amount) / float(g.target_amount) * 100
        deadline = f" (до {g.deadline})" if g.deadline else ""
        lines.append(f"🎯 {g.name}{deadline}")
        lines.append(f"   {float(g.current_amount):,.0f} / {float(g.target_amount):,.0f} ₽ — {pct:.0f}%\n")
    await callback.message.edit_text("\n".join(lines), reply_markup=savings_menu_kb())
    await callback.answer()


# ── Новая цель ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "sav_new")
async def cb_savings_new(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SavingsStates.goal_name)
    await state.update_data(msg_id=callback.message.message_id)
    await callback.message.edit_text(
        "Как назовём цель?\n(например: ноутбук, отпуск, подушка безопасности)",
        reply_markup=prompt_kb("sav_m"),
    )
    await callback.answer()


@router.message(SavingsStates.goal_name)
async def process_goal_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(goal_name=message.text.strip())
    await state.set_state(SavingsStates.goal_amount)
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text=f"Сколько копим на «{message.text.strip()}»? (₽):",
        reply_markup=prompt_kb("sav_m"),
    )
    await message.delete()


@router.message(SavingsStates.goal_amount)
async def process_goal_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.delete()
        return
    data = await state.get_data()
    await state.update_data(goal_amount=amount)
    await state.set_state(SavingsStates.goal_deadline)
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text="Есть дедлайн? Введи дату ДД.ММ.ГГГГ или напиши «нет»:",
        reply_markup=prompt_kb("sav_m"),
    )
    await message.delete()


@router.message(SavingsStates.goal_deadline)
async def process_goal_deadline(message: Message, state: FSMContext, session: AsyncSession) -> None:
    deadline: date | None = None
    text = message.text.strip().lower()
    if text != "нет":
        try:
            parts = text.split(".")
            deadline = date(int(parts[2]), int(parts[1]), int(parts[0]))
        except (ValueError, IndexError):
            await message.delete()
            return
    data = await state.get_data()
    user = await user_service.get_or_create(session, message.from_user.id)
    goal = await goal_repo.create(session, user.id, data["goal_name"], data["goal_amount"], deadline)
    await session.commit()
    await state.clear()
    deadline_str = f" до {goal.deadline}" if goal.deadline else ""
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text=f"🏦 НАКОПИТЬ\n\nЦель «{goal.name}»{deadline_str} на {float(goal.target_amount):,.0f} ₽ создана ✓",
        reply_markup=savings_menu_kb(),
    )
    await message.delete()


# ── Пополнить цель ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "sav_add")
async def cb_savings_add(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await user_service.get_or_create(session, callback.from_user.id)
    goals = await goal_repo.get_all(session, user.id)
    if not goals:
        await callback.message.edit_text("Целей пока нет.", reply_markup=savings_menu_kb())
        await callback.answer()
        return
    await callback.message.edit_text(
        "Выбери цель для пополнения:", reply_markup=goals_list_kb(goals, "add")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sav_add_"))
async def cb_savings_add_goal(callback: CallbackQuery, state: FSMContext) -> None:
    goal_id = int(callback.data.split("_")[-1])
    await state.set_state(SavingsStates.add_amount)
    await state.update_data(goal_id=goal_id, msg_id=callback.message.message_id)
    await callback.message.edit_text(
        "Введи сумму пополнения (₽):\nОна будет списана с баланса и зачислена в копилку.",
        reply_markup=prompt_kb("sav_m"),
    )
    await callback.answer()


@router.message(SavingsStates.add_amount)
async def process_savings_add(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.delete()
        return
    data = await state.get_data()
    user = await user_service.get_or_create(session, message.from_user.id)

    goal = await goal_repo.get_by_id(session, data["goal_id"])
    new_current = float(goal.current_amount) + amount
    await goal_repo.update_current_amount(session, data["goal_id"], new_current)

    # Обновляем баланс
    balance = await balance_repo.get(session, user.id)
    if balance:
        await balance_repo.upsert(session, user.id, float(balance.amount) - amount)

    # Записываем в историю как расход
    await expense_repo.add_irregular(
        session, user.id,
        category=f"Копилка: {goal.name}",
        amount=amount,
        is_mandatory=False,
    )

    await session.commit()
    await state.clear()
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=data["msg_id"],
        text=f"🏦 НАКОПИТЬ\n\n{amount:,.0f} ₽ добавлено в копилку ✓\nНакоплено: {new_current:,.0f} ₽",
        reply_markup=savings_menu_kb(),
    )
    await message.delete()


# ── Удалить цель ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "sav_del")
async def cb_savings_del(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await user_service.get_or_create(session, callback.from_user.id)
    goals = await goal_repo.get_all(session, user.id)
    if not goals:
        await callback.message.edit_text("Целей пока нет.", reply_markup=savings_menu_kb())
        await callback.answer()
        return
    await callback.message.edit_text(
        "Выбери цель для удаления:", reply_markup=goals_list_kb(goals, "del")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sav_del_") & ~F.data.startswith("sav_del_ok_"))
async def cb_savings_del_confirm(callback: CallbackQuery) -> None:
    goal_id = int(callback.data.split("_")[-1])
    await callback.message.edit_text(
        "Удалить цель? Накопленные деньги вернутся на баланс.",
        reply_markup=confirm_delete_goal_kb(goal_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sav_del_ok_"))
async def cb_savings_del_ok(callback: CallbackQuery, session: AsyncSession) -> None:
    goal_id = int(callback.data.split("_")[-1])
    user = await user_service.get_or_create(session, callback.from_user.id)
    goal = await goal_repo.get_by_id(session, goal_id)
    returned = float(goal.current_amount) if goal and goal.current_amount else 0.0
    if returned > 0:
        balance = await balance_repo.get(session, user.id)
        if balance:
            await balance_repo.upsert(session, user.id, float(balance.amount) + returned)
        # Записываем возврат в историю как доход
        await income_repo.add_irregular(
            session, user.id,
            source=f"Возврат из копилки: {goal.name}",
            amount=returned,
        )
    await goal_repo.delete(session, goal_id)
    await session.commit()
    await callback.message.edit_text(
        "🏦 НАКОПИТЬ\n\nЦель удалена, деньги возвращены на баланс ✓",
        reply_markup=savings_menu_kb(),
    )
    await callback.answer()
