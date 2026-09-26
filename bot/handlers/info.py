from datetime import date

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.menus import back_only_kb
from db.repos import balance_repo, income_repo, expense_repo, goal_repo
from ai.finance import get_next_income_info, get_next_expense_info
from services import user_service

router = Router()


@router.callback_query(F.data == "info")
async def cb_info(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await user_service.get_or_create(session, callback.from_user.id)
    today = date.today()

    balance    = await balance_repo.get(session, user.id)
    inc_rows   = await income_repo.get_regular(session, user.id)
    exp_rows   = await expense_repo.get_regular(session, user.id)
    goals      = await goal_repo.get_all(session, user.id)

    inc_list = [{"source": r.source, "amount": float(r.amount), "pay_day": r.pay_day} for r in inc_rows]
    exp_list = [{"name": e.name, "amount": float(e.amount), "charge_day": e.charge_day} for e in exp_rows]

    next_inc = get_next_income_info(inc_list, today)
    next_exp = get_next_expense_info(exp_list, today)

    lines = ["📊 ОБЩАЯ ИНФОРМАЦИЯ\n"]

    if inc_rows:
        lines.append("📈 Постоянные доходы:")
        for r in inc_rows:
            lines.append(f"  {r.source} — {float(r.amount):,.0f} ₽ (день {r.pay_day})")
        lines.append(f"  Итого: {sum(float(r.amount) for r in inc_rows):,.0f} ₽\n")

    if exp_rows:
        lines.append("📉 Постоянные расходы:")
        for e in exp_rows:
            lines.append(f"  {e.name} — {float(e.amount):,.0f} ₽ (день {e.charge_day})")
        lines.append(f"  Итого: {sum(float(e.amount) for e in exp_rows):,.0f} ₽\n")

    bal = float(balance.amount) if balance else 0.0
    lines.append(f"💰 Текущий баланс: {bal:,.0f} ₽")

    for g in goals:
        pct = float(g.current_amount) / float(g.target_amount) * 100 if g.target_amount else 0
        lines.append(f"🎯 {g.name}: {float(g.current_amount):,.0f} / {float(g.target_amount):,.0f} ₽ ({pct:.0f}%)")

    if next_inc["next_income_source"]:
        lines.append(f"\n📅 Ближайший доход: {next_inc['next_income_source']} — через {next_inc['days_until_income']} дн.")

    if next_exp["next_expense_name"]:
        lines.append(
            f"⚠️ Ближайшая трата: {next_exp['next_expense_name']} "
            f"{float(next_exp['next_expense_amount']):,.0f} ₽ — через {next_exp['days_until_expense']} дн."
        )

    await callback.message.edit_text("\n".join(lines), reply_markup=back_only_kb("mm"))
    await callback.answer()
