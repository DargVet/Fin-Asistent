from datetime import date, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.menus import history_menu_kb, back_only_kb
from db.repos import income_repo, expense_repo
from services import user_service

router = Router()


async def _format_history(user_id: int, session: AsyncSession, from_date: date, label: str) -> str:
    today = date.today()
    incomes  = await income_repo.get_irregular(session, user_id, from_date, today)
    expenses = await expense_repo.get_irregular(session, user_id, from_date, today)

    lines = [f"📜 ИСТОРИЯ — {label}\n"]

    if incomes:
        lines.append("📥 Доходы:")
        for r in incomes:
            lines.append(f"  {r.source} — +{float(r.amount):,.0f} ₽")
        lines.append(f"  Итого: +{sum(float(r.amount) for r in incomes):,.0f} ₽\n")

    if expenses:
        lines.append("📤 Расходы:")
        for e in expenses:
            lines.append(f"  {e.category} — -{float(e.amount):,.0f} ₽")
        lines.append(f"  Итого: -{sum(float(e.amount) for e in expenses):,.0f} ₽")

    if not incomes and not expenses:
        lines.append("Операций нет.")

    return "\n".join(lines)


@router.callback_query(F.data == "hist_m")
async def cb_history_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text("📜 ИСТОРИЯ\n\nВыбери период:", reply_markup=history_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "hist_t")
async def cb_history_today(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await user_service.get_or_create(session, callback.from_user.id)
    text = await _format_history(user.id, session, date.today(), "Сегодня")
    await callback.message.edit_text(text, reply_markup=back_only_kb("hist_m"))
    await callback.answer()


@router.callback_query(F.data == "hist_w")
async def cb_history_week(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await user_service.get_or_create(session, callback.from_user.id)
    text = await _format_history(user.id, session, date.today() - timedelta(days=7), "Неделя")
    await callback.message.edit_text(text, reply_markup=back_only_kb("hist_m"))
    await callback.answer()


@router.callback_query(F.data == "hist_mo")
async def cb_history_month(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await user_service.get_or_create(session, callback.from_user.id)
    text = await _format_history(user.id, session, date.today() - timedelta(days=30), "Месяц")
    await callback.message.edit_text(text, reply_markup=back_only_kb("hist_m"))
    await callback.answer()
