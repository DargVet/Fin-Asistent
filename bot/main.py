import asyncio
import logging
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import BOT_TOKEN
from bot.handlers import start, main_menu, income, expenses, balance, savings, info, history, settings, chat
from bot.middlewares.db import DatabaseMiddleware
from scheduler.tasks import setup_scheduler

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(DatabaseMiddleware())

    # Порядок важен: chat — последним (catch-all)
    dp.include_router(start.router)
    dp.include_router(main_menu.router)
    dp.include_router(income.router)
    dp.include_router(expenses.router)
    dp.include_router(balance.router)
    dp.include_router(savings.router)
    dp.include_router(info.router)
    dp.include_router(history.router)
    dp.include_router(settings.router)
    dp.include_router(chat.router)

    scheduler = setup_scheduler()
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
