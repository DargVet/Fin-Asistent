from datetime import date

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from services import goal_service, user_service

router = Router()


class GoalStates(StatesGroup):
    name = State()
    amount = State()
    deadline = State()


# ── Список целей ──────────────────────────────────────────────────────────────

@router.message(Command("goals"))
@router.message(F.text == "🎯 Цели")
async def cmd_goals(message: Message, session: AsyncSession) -> None:
    user = await user_service.get_or_create(session, message.from_user.id)
    goals = await goal_service.get_all(session, user.id)

    if not goals:
        await message.answer(
            "Целей пока нет. Создай первую командой /add_goal"
        )
        return

    lines = ["Твои цели:\n"]
    for g in goals:
        progress = float(g.current_amount) / float(g.target_amount) * 100
        deadline_str = f" (до {g.deadline})" if g.deadline else ""
        lines.append(
            f"• {g.name}{deadline_str}\n"
            f"  {g.current_amount:,.0f} / {g.target_amount:,.0f} ₽ — {progress:.0f}%"
        )

    await message.answer("\n".join(lines))


# ── Создание цели (FSM) ───────────────────────────────────────────────────────

@router.message(Command("add_goal"))
async def cmd_add_goal(message: Message, state: FSMContext) -> None:
    await state.set_state(GoalStates.name)
    await message.answer("Как назовём цель? (например: ноутбук, отпуск, подушка безопасности)")


@router.message(GoalStates.name)
async def process_goal_name(message: Message, state: FSMContext) -> None:
    await state.update_data(goal_name=message.text.strip())
    await state.set_state(GoalStates.amount)
    await message.answer("На какую сумму копим? (₽):")


@router.message(GoalStates.amount)
async def process_goal_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.answer("Введи сумму цифрами, например: 60000")
        return

    await state.update_data(goal_amount=amount)
    await state.set_state(GoalStates.deadline)
    await message.answer(
        "Есть дедлайн? Введи дату в формате ДД.ММ.ГГГГ или напиши «нет»:"
    )


@router.message(GoalStates.deadline)
async def process_goal_deadline(message: Message, state: FSMContext, session: AsyncSession) -> None:
    deadline: date | None = None
    text = message.text.strip().lower()

    if text != "нет":
        try:
            deadline = date(*reversed([int(x) for x in text.split(".")]))
        except (ValueError, TypeError):
            await message.answer("Не понял дату. Введи в формате ДД.ММ.ГГГГ или напиши «нет»:")
            return

    data = await state.get_data()
    user = await user_service.get_or_create(session, message.from_user.id)
    goal = await goal_service.create(
        session,
        user_id=user.id,
        name=data["goal_name"],
        target_amount=data["goal_amount"],
        deadline=deadline,
    )

    await state.clear()
    deadline_str = f" до {goal.deadline}" if goal.deadline else ""
    await message.answer(
        f"Цель «{goal.name}»{deadline_str} на {goal.target_amount:,.0f} ₽ создана ✓\n\n"
        "Можешь спросить меня: «Когда я накоплю на ноутбук?»"
    )
