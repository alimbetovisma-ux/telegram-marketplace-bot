"""Background job bodies for APScheduler (wired up in main.py). Each opens
its own short-lived DB session since APScheduler jobs run independently of
any request/update lifecycle."""

from __future__ import annotations

import logging

from db.session import SessionLocal
from bot.services import fulfillment, ton_monitor

logger = logging.getLogger(__name__)


async def poll_ton() -> None:
    async with SessionLocal() as session:
        try:
            await ton_monitor.poll_once(session)
        except Exception:
            logger.exception("poll_ton job failed")


async def expire_ton_requests() -> None:
    async with SessionLocal() as session:
        try:
            await ton_monitor.expire_stale_requests(session)
        except Exception:
            logger.exception("expire_ton_requests job failed")


async def expire_rentals() -> None:
    async with SessionLocal() as session:
        try:
            await fulfillment.expire_rentals(session)
        except Exception:
            logger.exception("expire_rentals job failed")
