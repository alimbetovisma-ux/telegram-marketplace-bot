"""Receiving side of TON/USDT top-ups and sells.

Polls the TonAPI REST API (https://tonapi.io) for the hot wallet's recent
incoming transfers and matches them against pending TonTopupRequest rows by
the unique memo/comment the user was asked to include. TonAPI returns
already-decoded JSON (amount, sender, comment) so this avoids hand-parsing
raw TON cells, unlike the low-level tonutils client.

NOTE: not executed/tested locally (no Python runtime in the environment that
wrote this). Verify with a small real deposit before trusting it in
production -- if TonAPI ever changes its action JSON shape, matching will
simply fail closed (no credit), never mis-credit, since it only acts on an
exact memo match.
"""

from __future__ import annotations

import logging
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.services import credit_balance
from bot.services.ton_wallet import DEFAULT_USDT_MASTER, get_wallet_address
from db.models import TonDirection, TonRequestStatus, TonTopupRequest, TxType, User

logger = logging.getLogger(__name__)

TONAPI_BASE = "https://tonapi.io"

_cached_address: str | None = None


async def _wallet_address() -> str | None:
    global _cached_address
    if _cached_address:
        return _cached_address
    if not settings.ton_enabled:
        return None
    try:
        _cached_address = await get_wallet_address()
    except Exception:
        logger.exception("Failed to derive TON wallet address")
        return None
    return _cached_address


def _rate_for(currency: str) -> Decimal:
    return settings.ton_rate_uzs if currency == "TON" else settings.usdt_rate_uzs


async def _fetch_recent_events(address: str, limit: int = 30) -> list[dict]:
    headers = {}
    if settings.ton_api_key:
        headers["Authorization"] = f"Bearer {settings.ton_api_key}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{TONAPI_BASE}/v2/accounts/{address}/events", params={"limit": limit}, headers=headers)
        resp.raise_for_status()
        return resp.json().get("events", [])


def _iter_incoming_transfers(events: list[dict]):
    """Yield (currency, amount, comment, event_id) for TON/USDT transfers in."""
    for event in events:
        event_id = event.get("event_id", "")
        for action in event.get("actions", []):
            if action.get("status") != "ok":
                continue
            if action.get("type") == "TonTransfer":
                data = action.get("TonTransfer", {})
                amount = Decimal(data.get("amount", 0)) / Decimal(10**9)
                yield "TON", amount, data.get("comment") or "", event_id
            elif action.get("type") == "JettonTransfer":
                data = action.get("JettonTransfer", {})
                jetton = data.get("jetton", {})
                if jetton.get("address") != DEFAULT_USDT_MASTER:
                    continue
                decimals = int(jetton.get("decimals", 6))
                amount = Decimal(data.get("amount", 0)) / Decimal(10**decimals)
                yield "USDT", amount, data.get("comment") or "", event_id


async def poll_once(session: AsyncSession) -> int:
    """Check for confirmations. Returns how many requests were credited."""
    if not settings.ton_enabled:
        return 0

    address = await _wallet_address()
    if not address:
        return 0

    result = await session.execute(select(TonTopupRequest).where(TonTopupRequest.status == TonRequestStatus.PENDING))
    pending = {req.memo: req for req in result.scalars().all()}
    if not pending:
        return 0

    try:
        events = await _fetch_recent_events(address)
    except Exception:
        logger.exception("TonAPI poll failed")
        return 0

    credited = 0
    for currency, amount, comment, event_id in _iter_incoming_transfers(events):
        req = pending.get(comment.strip())
        if req is None or req.currency != currency:
            continue
        if amount < req.expected_amount * Decimal("0.99"):
            continue  # underpaid -- leave pending, admin can sort it out manually

        user = await session.get(User, req.user_id)
        if user is None:
            continue

        rate = _rate_for(currency)
        credited_uzs = amount * rate
        tx_type = TxType.TOPUP_CRYPTO
        if req.direction == TonDirection.SELL:
            credited_uzs = credited_uzs * (Decimal("1") - settings.p2p_commission_percent / Decimal("100"))
            tx_type = TxType.SELL_CRYPTO
        credited_uzs = credited_uzs.quantize(Decimal("1"))

        req.status = TonRequestStatus.CONFIRMED
        req.tx_hash = event_id
        req.credited_uzs = credited_uzs
        from datetime import datetime, timezone

        req.confirmed_at = datetime.now(timezone.utc)

        await credit_balance(session, user, credited_uzs, tx_type, currency=currency, meta={"memo": req.memo, "amount": str(amount)})
        await session.commit()
        credited += 1

        try:
            from bot.bot_instance import bot
            from bot.locales import t

            await bot.send_message(
                user.tg_id,
                t(user.language, "topup_confirmed", amount=str(credited_uzs), balance=str(user.balance)),
            )
        except Exception:
            logger.exception("Failed to notify user about TON credit")

    return credited


async def expire_stale_requests(session: AsyncSession) -> None:
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.ton_request_ttl_minutes)
    result = await session.execute(
        select(TonTopupRequest).where(TonTopupRequest.status == TonRequestStatus.PENDING, TonTopupRequest.created_at < cutoff)
    )
    stale = result.scalars().all()
    for req in stale:
        req.status = TonRequestStatus.EXPIRED
    if stale:
        await session.commit()
