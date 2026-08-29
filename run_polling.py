"""Local dev entrypoint: runs the bot via long polling (no HTTPS/webhook needed).

Use this while developing on localhost. In production (docker-compose), the
bot runs via webhook inside main.py/uvicorn instead -- don't run both against
the same bot token at the same time.
"""

import asyncio
import logging

import bot.runtime as runtime
from bot.bot_instance import bot
from bot.handlers import main_router
from bot.middlewares.auth import AuthMiddleware
from aiogram import Dispatcher

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(main_router)
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    me = await bot.get_me()
    runtime.bot_username = me.username or ""
    logging.info("Starting polling as @%s", runtime.bot_username)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
