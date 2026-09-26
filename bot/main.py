import asyncio
import logging
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import BOT_TOKEN
from bot.handlers import start, setup, goals, chat
from bot.middlewares.db import DatabaseMiddleware
from scheduler.tasks import setup_scheduler

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware — сессия БД на каждый апдейт
    dp.update.middleware(DatabaseMiddleware())

    # Роутеры — порядок важен: chat идёт последним (catch-all)
    dp.include_router(start.router)
    dp.include_router(setup.router)
    dp.include_router(goals.router)
    dp.include_router(chat.router)

    # Планировщик
    scheduler = setup_scheduler()
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
