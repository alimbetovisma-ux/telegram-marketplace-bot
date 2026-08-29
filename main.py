import logging
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram import Dispatcher
from aiogram.types import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import bot.runtime as runtime
from admin.routes import router as admin_router
from api.routers import catalog, orders, profile, wallet
from bot.bot_instance import bot
from bot.config import settings
from bot.handlers import main_router
from bot.middlewares.auth import AuthMiddleware
from bot.services import jobs

logging.basicConfig(level=logging.INFO)

dp = Dispatcher()
dp.include_router(main_router)
dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())


scheduler = AsyncIOScheduler()


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

    if settings.ton_enabled:
        scheduler.add_job(jobs.poll_ton, "interval", seconds=settings.ton_monitor_interval_seconds, id="poll_ton")
        scheduler.add_job(jobs.expire_ton_requests, "interval", minutes=10, id="expire_ton_requests")
    scheduler.add_job(jobs.expire_rentals, "interval", minutes=30, id="expire_rentals")
    scheduler.start()

    yield

    scheduler.shutdown(wait=False)
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
app.include_router(admin_router)


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
