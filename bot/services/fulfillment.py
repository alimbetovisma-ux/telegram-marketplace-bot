"""Orchestrates automatic order fulfillment, with a hard rule: any failure,
timeout, or missing configuration silently falls back to the existing
manual-admin flow from Stage 1 (order just stays `paid_awaiting_fulfillment`,
same as before this module existed). The buyer's money is never at risk --
worst case, delivery is slower and an admin does it by hand.

Called by the purchase callers (bot/handlers/catalog.py, api/routers/orders.py)
right after they commit a paid order.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.services import fragment_client
from db.models import Category, Order, OrderStatus, RentalAsset, RentalAssetStatus, User

logger = logging.getLogger(__name__)


async def try_auto_fulfill(session: AsyncSession, order: Order, item, buyer: User) -> bool:
    """Attempt automatic fulfillment for the given (already paid) order.

    Returns True if fulfilled automatically, False if it should wait for an
    admin (the order is left untouched in that case).
    """
    try:
        if item.category == Category.PREMIUM:
            return await _fulfill_premium(session, order, item, buyer)
        if item.category == Category.STARS:
            return await _fulfill_stars(session, order, item, buyer)
        if item.category in Category.RENTAL:
            return await _fulfill_rental(session, order, item)
    except Exception:
        logger.exception("Auto-fulfillment crashed for order #%s", order.id)
    return False


def _months_from_item(item) -> int | None:
    opts = item.duration_options or {}
    months = opts.get("months")
    return int(months) if months in (3, 6, 12) else None


def _stars_from_item(item) -> int | None:
    opts = item.duration_options or {}
    stars = opts.get("stars")
    return int(stars) if isinstance(stars, int) and 50 <= stars <= 10_000_000 else None


async def _fulfill_premium(session: AsyncSession, order: Order, item, buyer: User) -> bool:
    if not settings.fragment_enabled:
        return False
    target = order.target_username or buyer.username
    months = _months_from_item(item)
    if not target or not months:
        logger.info("Order #%s: missing target_username or months, skip auto-fulfill", order.id)
        return False

    try:
        result = await asyncio.wait_for(
            fragment_client.buy_premium(target, months), timeout=settings.fragment_timeout_seconds
        )
    except Exception as exc:
        logger.warning("Fragment premium purchase failed for order #%s: %s", order.id, exc)
        order.fulfillment_note = f"Fragment auto-buy failed: {exc}"
        await session.commit()
        return False

    await _mark_fulfilled(session, order, f"Fragment tx {result.transaction_id} ({months} months -> @{result.username})")
    await _notify_buyer_fulfilled(buyer, order)
    return True


async def _fulfill_stars(session: AsyncSession, order: Order, item, buyer: User) -> bool:
    if not settings.fragment_enabled:
        return False
    target = order.target_username or buyer.username
    stars = _stars_from_item(item)
    if not target or not stars:
        logger.info("Order #%s: missing target_username or stars amount, skip auto-fulfill", order.id)
        return False

    try:
        result = await asyncio.wait_for(
            fragment_client.buy_stars(target, stars), timeout=settings.fragment_timeout_seconds
        )
    except Exception as exc:
        logger.warning("Fragment stars purchase failed for order #%s: %s", order.id, exc)
        order.fulfillment_note = f"Fragment auto-buy failed: {exc}"
        await session.commit()
        return False

    await _mark_fulfilled(session, order, f"Fragment tx {result.transaction_id} ({stars} stars -> @{result.username})")
    await _notify_buyer_fulfilled(buyer, order)
    return True


async def _fulfill_rental(session: AsyncSession, order: Order, item) -> bool:
    result = await session.execute(
        select(RentalAsset)
        .where(RentalAsset.catalog_item_id == item.id, RentalAsset.status == RentalAssetStatus.AVAILABLE)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        return False

    days = (item.duration_options or {}).get("days") or 30
    asset.status = RentalAssetStatus.RENTED
    asset.current_order_id = order.id
    asset.rented_until = datetime.now(timezone.utc) + timedelta(days=int(days))
    order.duration_days = int(days)

    await _mark_fulfilled(session, order, f"Auto-assigned rental asset #{asset.id}, until {asset.rented_until:%Y-%m-%d}")

    buyer = await session.get(User, order.user_id)
    try:
        from bot.bot_instance import bot

        await bot.send_message(
            buyer.tg_id,
            f"✅ {item.title}\n\n{asset.access_payload}\n\n"
            f"Amal qilish muddati / Действует до: {asset.rented_until:%Y-%m-%d %H:%M} UTC",
        )
    except Exception:
        logger.exception("Failed to deliver rental asset to buyer for order #%s", order.id)

    return True


async def _mark_fulfilled(session: AsyncSession, order: Order, note: str) -> None:
    order.status = OrderStatus.FULFILLED
    order.fulfillment_note = note
    order.fulfilled_at = datetime.now(timezone.utc)
    await session.commit()


async def _notify_buyer_fulfilled(buyer: User, order: Order) -> None:
    try:
        from bot.bot_instance import bot
        from bot.locales import t

        await bot.send_message(buyer.tg_id, t(buyer.language, "order_fulfilled_notify", order_id=order.id))
    except Exception:
        logger.exception("Failed to notify buyer #%s about order #%s", buyer.id, order.id)


async def expire_rentals(session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(RentalAsset).where(RentalAsset.status == RentalAssetStatus.RENTED, RentalAsset.rented_until < now)
    )
    expired = result.scalars().all()
    if not expired:
        return

    for asset in expired:
        asset.status = RentalAssetStatus.RETIRED
    await session.commit()

    try:
        from bot.bot_instance import bot

        for asset in expired:
            for admin_id in settings.admin_id_list:
                try:
                    await bot.send_message(
                        admin_id,
                        f"⏰ Ijara muddati tugadi: asset #{asset.id} (buyurtma #{asset.current_order_id}). "
                        f"Aktivni qayta tiklang yoki yangisini qo'shing.",
                    )
                except Exception:
                    pass
    except Exception:
        logger.exception("Failed to notify admins about expired rentals")
