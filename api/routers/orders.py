from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.schemas import OrderOut
from bot.bot_instance import bot
from bot.config import settings
from bot.locales import t
from bot.services import InsufficientBalance, ItemUnavailable, fmt_money, purchase_item
from bot.services import fulfillment
from db.models import CatalogItem, Order, User
from db.session import get_session

router = APIRouter(prefix="/api/orders", tags=["orders"])


class CreateOrderIn(BaseModel):
    catalog_item_id: int


def _to_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        catalog_item_id=order.catalog_item_id,
        item_title=order.item.title,
        qty=order.qty,
        total_uzs=order.total_uzs,
        status=order.status,
        created_at=order.created_at,
    )


@router.get("", response_model=list[OrderOut])
async def list_orders(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[OrderOut]:
    result = await session.execute(
        select(Order).where(Order.user_id == user.id).options(selectinload(Order.item)).order_by(Order.id.desc())
    )
    return [_to_out(o) for o in result.scalars().all()]


@router.post("", response_model=OrderOut)
async def create_order(
    payload: CreateOrderIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> OrderOut:
    item = await session.get(CatalogItem, payload.catalog_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        order, bonus_info = await purchase_item(session, user, item, target_username=user.username)
    except ItemUnavailable:
        raise HTTPException(status_code=409, detail="Item unavailable")
    except InsufficientBalance:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    await session.commit()
    await session.refresh(order)
    order.item = item

    auto_fulfilled = await fulfillment.try_auto_fulfill(session, order, item, user)
    if not auto_fulfilled:
        buyer_name = f"@{user.username}" if user.username else (user.first_name or str(user.tg_id))
        for admin_id in settings.admin_id_list:
            try:
                await bot.send_message(
                    admin_id,
                    t("ru", "admin_new_order_notify", user=buyer_name, title=item.title, total=fmt_money(order.total_uzs), order_id=order.id),
                )
            except Exception:
                pass
    if bonus_info:
        referrer, bonus = bonus_info
        try:
            await bot.send_message(referrer.tg_id, t(referrer.language, "referral_bonus_earned", amount=fmt_money(bonus)))
        except Exception:
            pass

    return _to_out(order)
