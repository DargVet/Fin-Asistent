from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db.session import AsyncSessionFactory
from db.repos import balance_repo, expense_repo, income_repo

scheduler = AsyncIOScheduler()


async def _notify_upcoming_charges():
    """
    Запускается ежедневно. Находит пользователей, у которых сегодня
    списывается регулярный расход (charge_day == today), и может
    отправить уведомление через бота (подключить позже).
    """
    from datetime import date
    today = date.today()

    async with AsyncSessionFactory() as session:
        # TODO: подключить отправку уведомлений через бота
        pass


def setup_scheduler() -> AsyncIOScheduler:
    scheduler.add_job(
        _notify_upcoming_charges,
        trigger="cron",
        hour=9,
        minute=0,
        id="daily_charge_check",
        replace_existing=True,
    )
    return scheduler
