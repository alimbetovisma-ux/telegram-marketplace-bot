from decimal import Decimal
from typing import Annotated

from aiogram.types import LabeledPrice
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.schemas import CardTopupRequestIn, CardTopupRequestOut, StarsTopupIn, StarsTopupOut, TransactionOut
from bot.bot_instance import bot
from bot.config import settings
from bot.locales import t
from bot.runtime import bot_username
from bot.services import create_card_topup_request, fmt_money, get_setting
from db.models import Transaction, User
from db.session import get_session

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


class BalanceOut(BaseModel):
    balance: Decimal


@router.get("", response_model=BalanceOut)
async def get_wallet(user: Annotated[User, Depends(get_current_user)]) -> BalanceOut:
    return BalanceOut(balance=user.balance)


@router.get("/history", response_model=list[TransactionOut])
async def get_history(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[Transaction]:
    result = await session.execute(select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.id.desc()).limit(50))
    return list(result.scalars().all())


@router.post("/topup/card", response_model=CardTopupRequestOut)
async def topup_card(
    payload: CardTopupRequestIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> CardTopupRequestOut:
    if payload.amount_uzs <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    req = await create_card_topup_request(session, user, payload.amount_uzs)
    await session.commit()
    await session.refresh(req)

    card_number = await get_setting(session, "card_number", settings.card_number)
    card_holder = await get_setting(session, "card_holder", settings.card_holder)
    return CardTopupRequestOut(
        request_id=req.id,
        amount_uzs=req.amount_uzs,
        card_number=card_number,
        card_holder=card_holder,
        bot_deeplink=f"https://t.me/{bot_username or 'your_bot'}",
    )


@router.post("/topup/stars", response_model=StarsTopupOut)
async def topup_stars(
    payload: StarsTopupIn,
    user: Annotated[User, Depends(get_current_user)],
) -> StarsTopupOut:
    if payload.amount_uzs <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    stars = int((payload.amount_uzs / settings.stars_to_uzs_rate).to_integral_value(rounding="ROUND_CEILING"))
    stars = max(stars, 1)
    lang = user.language
    link = await bot.create_invoice_link(
        title=t(lang, "stars_invoice_title"),
        description=t(lang, "stars_invoice_desc", stars=stars, amount=fmt_money(payload.amount_uzs)),
        payload=f"topup_stars:{payload.amount_uzs}",
        currency="XTR",
        prices=[LabeledPrice(label=t(lang, "stars_invoice_title"), amount=stars)],
        provider_token="",
    )
    return StarsTopupOut(stars=stars, invoice_link=link)
