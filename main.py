import logging
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram import Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import bot.runtime as runtime
from api.routers import catalog, orders, profile, wallet
from bot.bot_instance import bot
from bot.config import settings
from bot.handlers import main_router
from bot.middlewares.auth import AuthMiddleware

logging.basicConfig(level=logging.INFO)

dp = Dispatcher()
dp.include_router(main_router)
dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())


@asynccontextmanager
async def lifespan(_app: FastAPI):
    me = await bot.get_me()
    runtime.bot_username = me.username or ""

    if settings.public_url.startswith("https://"):
        await bot.set_webhook(
            url=f"{settings.public_url}{settings.webhook_path}",
            secret_token=settings.webhook_secret,
            allowed_updates=dp.resolve_used_update_types(),
        )
    yield
    await bot.session.close()


app = FastAPI(title="Telegram Marketplace", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router)
app.include_router(orders.router)
app.include_router(wallet.router)
app.include_router(profile.router)


@app.post(settings.webhook_path)
async def telegram_webhook(request: Request) -> Response:
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != settings.webhook_secret:
        return Response(status_code=401)
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return Response(status_code=200)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


webapp_dist = Path(__file__).parent / "webapp" / "dist"
if webapp_dist.exists():
    app.mount("/app", StaticFiles(directory=str(webapp_dist), html=True), name="webapp")
