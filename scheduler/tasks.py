from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db.session import AsyncSessionFactory
from db.repos import balance_repo, expense_repo, income_repo

scheduler = AsyncIOScheduler()


async def _apply_regular_transactions():
    """
    Запускается ежедневно. Начисляет регулярные доходы и списывает регулярные расходы
    в нужные дни месяца.
    """
    from datetime import date
    today = date.today()

    async with AsyncSessionFactory() as session:
        # Доходы
        result = await session.execute(
            __import__("sqlalchemy", fromlist=["select"]).select(
                __import__("db.models", fromlist=["IncomeRegular"]).IncomeRegular
            ).where(
                __import__("db.models", fromlist=["IncomeRegular"]).IncomeRegular.pay_day == today.day
            )
        )
        for income in result.scalars().all():
            balance = await balance_repo.get(session, income.user_id)
            if balance:
                await balance_repo.upsert(session, income.user_id,
                                         float(balance.amount) + float(income.amount))

        # Расходы
        result = await session.execute(
            __import__("sqlalchemy", fromlist=["select"]).select(
                __import__("db.models", fromlist=["ExpenseRegular"]).ExpenseRegular
            ).where(
                __import__("db.models", fromlist=["ExpenseRegular"]).ExpenseRegular.charge_day == today.day
            )
        )
        for expense in result.scalars().all():
            balance = await balance_repo.get(session, expense.user_id)
            if balance:
                await balance_repo.upsert(session, expense.user_id,
                                         float(balance.amount) - float(expense.amount))

        await session.commit()


def setup_scheduler() -> AsyncIOScheduler:
    scheduler.add_job(
        _apply_regular_transactions,
        trigger="cron",
        hour=0,
        minute=0,
        id="daily_transactions",
        replace_existing=True,
    )
    return scheduler
