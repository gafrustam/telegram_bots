"""
VPR Math Bot — main entry point.
"""

import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import common, stats, test, training

os.makedirs("logs", exist_ok=True)
_log_handler = RotatingFileHandler("logs/vpr_bot.log", maxBytes=5_000_000, backupCount=3)
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[_log_handler, logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    await init_db()
    logger.info("Database initialised")

    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers (order matters — more specific first)
    dp.include_router(common.router)
    dp.include_router(training.router)
    dp.include_router(test.router)
    dp.include_router(stats.router)

    logger.info("Starting polling…")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
