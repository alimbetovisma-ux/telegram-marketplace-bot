from decimal import Decimal, InvalidOperation

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.p2p import (
    admin_listing_review_kb,
    buyer_confirm_kb,
    listing_detail_kb,
    listing_list_kb,
    p2p_menu_kb,
    p2p_type_kb,
    seller_sent_kb,
)
from bot.locales import t
from bot.services import credit_balance, fmt_money
from bot.states import ListingStates, P2PDisputeStates
from db.models import DealStatus, Listing, ListingStatus, ListingType, P2PDeal, TxType, User

router = Router(name="p2p")


def _display_name(user: User) -> str:
    return f"@{user.username}" if user.username else (user.first_name or str(user.tg_id))


async def show_p2p(message: Message, user: User) -> None:
    lang = user.language
    await message.answer(f"{t(lang, 'p2p_title')}\n\n{t(lang, 'p2p_sub')}", reply_markup=p2p_menu_kb(lang))


@router.callback_query(F.data == "p2p:browse")
async def on_browse(callback: CallbackQuery, user: User) -> None:
    await callback.message.edit_text(t(user.language, "p2p_choose_browse_type"), reply_markup=p2p_type_kb(user.language, "p2p:browsetype"))
    await callback.answer()


@router.callback_query(F.data.startswith("p2p:browsetype:"))
async def on_browse_type(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    listing_type = callback.data.removeprefix("p2p:browsetype:")
    lang = user.language
    result = await session.execute(
        select(Listing).where(Listing.type == listing_type, Listing.status == ListingStatus.ACTIVE).order_by(Listing.id.desc())
    )
    listings = result.scalars().all()
    if not listings:
        await callback.message.edit_text(t(lang, "p2p_browse_empty"))
        await callback.answer()
        return

    pairs = [(listing.id, f"{listing.title} — {fmt_money(listing.price_uzs)} so'm") for listing in listings]
    await callback.message.edit_text(t(lang, "p2p_choose_browse_type"), reply_markup=listing_list_kb(pairs))
    await callback.answer()


@router.callback_query(F.data.startswith("p2p:view:"))
async def on_view(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    listing_id = int(callback.data.removeprefix("p2p:view:"))
    listing = await session.get(Listing, listing_id)
    lang = user.language
    if listing is None or listing.status != ListingStatus.ACTIVE:
        await callback.answer(t(lang, "p2p_browse_empty"), show_alert=True)
        return

    text = t(lang, "p2p_buy_confirm", title=listing.title, price=fmt_money(listing.price_uzs))
    if listing.description:
        text = f"{listing.title}\n{listing.description}\n\n{text}"
    await callback.message.answer(text, reply_markup=listing_detail_kb(lang, listing.id))
    await callback.answer()


@router.callback_query(F.data.startswith("p2p:buy:"))
async def on_buy(callback: CallbackQuery, user: User, session: AsyncSession, bot: Bot) -> None:
    listing_id = int(callback.data.removeprefix("p2p:buy:"))
    listing = await session.get(Listing, listing_id)
    lang = user.language
    if listing is None or listing.status != ListingStatus.ACTIVE:
        await callback.answer(t(lang, "p2p_browse_empty"), show_alert=True)
        return
    if listing.seller_id == user.id:
        await callback.answer()
        return
    if user.balance < listing.price_uzs:
        await callback.answer(t(lang, "insufficient_balance", price=fmt_money(listing.price_uzs), balance=fmt_money(user.balance)), show_alert=True)
        return

    price = listing.price_uzs
    commission = (price * settings.p2p_commission_percent / Decimal("100")).quantize(Decimal("1"))
    await credit_balance(session, user, -price, TxType.P2P_ESCROW, meta={"listing_id": listing.id})
    listing.status = ListingStatus.RESERVED
    deal = P2PDeal(listing_id=listing.id, buyer_id=user.id, escrow_uzs=price, commission_uzs=commission, status=DealStatus.AWAITING_TRANSFER)
    session.add(deal)
    await session.commit()
    await session.refresh(deal)

    seller = await session.get(User, listing.seller_id)
    await callback.message.answer(t(lang, "p2p_deal_created_buyer"))
    await callback.answer()

    try:
        await bot.send_message(
            seller.tg_id,
            t(seller.language, "p2p_deal_created_seller", title=listing.title, buyer=_display_name(user), price=fmt_money(price)),
            reply_markup=seller_sent_kb(seller.language, deal.id),
        )
    except Exception:
        pass


@router.callback_query(F.data == "p2p:sell")
async def on_sell_start(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.set_state(ListingStates.choosing_type)
    await callback.message.edit_text(t(user.language, "p2p_choose_type"), reply_markup=p2p_type_kb(user.language, "p2p:selltype"))
    await callback.answer()


@router.callback_query(F.data.startswith("p2p:selltype:"), ListingStates.choosing_type)
async def on_sell_type(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    listing_type = callback.data.removeprefix("p2p:selltype:")
    await state.update_data(type=listing_type)
    await state.set_state(ListingStates.entering_title)
    await callback.message.answer(t(user.language, "p2p_enter_title"))
    await callback.answer()


@router.message(ListingStates.entering_title)
async def on_sell_title(message: Message, user: User, state: FSMContext) -> None:
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(ListingStates.entering_price)
    await message.answer(t(user.language, "p2p_enter_price"))


@router.message(ListingStates.entering_price)
async def on_sell_price(message: Message, user: User, state: FSMContext) -> None:
    lang = user.language
    try:
        price = Decimal((message.text or "").strip().replace(" ", "").replace(",", ""))
        if price <= 0:
            raise InvalidOperation
    except InvalidOperation:
        await message.answer(t(lang, "invalid_amount"))
        return
    await state.update_data(price=str(price))
    await state.set_state(ListingStates.entering_description)
    await message.answer(t(lang, "p2p_enter_description"))


@router.message(ListingStates.entering_description)
async def on_sell_description(message: Message, user: User, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    lang = user.language
    description = None if (message.text or "").strip() == "/skip" else (message.text or "").strip()
    data = await state.get_data()

    listing = Listing(
        seller_id=user.id,
        type=data["type"],
        title=data["title"],
        description=description,
        price_uzs=Decimal(data["price"]),
        status=ListingStatus.PENDING_REVIEW,
    )
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    await state.clear()

    await message.answer(t(lang, "p2p_listing_created"))

    type_label = "NFT" if listing.type == ListingType.NFT_GIFT else "username"
    for admin_id in settings.admin_id_list:
        try:
            await bot.send_message(
                admin_id,
                t("ru", "p2p_admin_new_listing", user=_display_name(user), title=listing.title, type=type_label, price=fmt_money(listing.price_uzs), listing_id=listing.id),
                reply_markup=admin_listing_review_kb(listing.id),
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("p2p:deal:sent:"))
async def on_deal_sent(callback: CallbackQuery, user: User, session: AsyncSession, bot: Bot) -> None:
    deal_id = int(callback.data.removeprefix("p2p:deal:sent:"))
    deal = await session.get(P2PDeal, deal_id, options=[selectinload(P2PDeal.listing)])
    if deal is None or deal.status != DealStatus.AWAITING_TRANSFER or deal.listing.seller_id != user.id:
        await callback.answer()
        return

    deal.status = DealStatus.AWAITING_CONFIRMATION
    await session.commit()
    await callback.message.edit_text(t(user.language, "p2p_deal_sent_seller"))
    await callback.answer()

    buyer = await session.get(User, deal.buyer_id)
    try:
        await bot.send_message(
            buyer.tg_id,
            t(buyer.language, "p2p_deal_sent_buyer", title=deal.listing.title),
            reply_markup=buyer_confirm_kb(buyer.language, deal.id),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("p2p:deal:confirm:"))
async def on_deal_confirm(callback: CallbackQuery, user: User, session: AsyncSession, bot: Bot) -> None:
    deal_id = int(callback.data.removeprefix("p2p:deal:confirm:"))
    deal = await session.get(P2PDeal, deal_id, options=[selectinload(P2PDeal.listing)])
    if deal is None or deal.status != DealStatus.AWAITING_CONFIRMATION or deal.buyer_id != user.id:
        await callback.answer()
        return

    from datetime import datetime, timezone

    deal.status = DealStatus.COMPLETED
    deal.confirmed_at = datetime.now(timezone.utc)
    deal.listing.status = ListingStatus.SOLD

    seller = await session.get(User, deal.listing.seller_id)
    payout = deal.escrow_uzs - deal.commission_uzs
    await credit_balance(session, seller, payout, TxType.P2P_RELEASE, meta={"deal_id": deal.id})
    await session.commit()

    await callback.message.edit_text(t(user.language, "p2p_deal_completed_buyer"))
    await callback.answer()

    try:
        await bot.send_message(
            seller.tg_id,
            t(seller.language, "p2p_deal_completed_seller", amount=fmt_money(payout), percent=settings.p2p_commission_percent),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("p2p:deal:dispute:"))
async def on_deal_dispute(callback: CallbackQuery, user: User, session: AsyncSession, state: FSMContext) -> None:
    deal_id = int(callback.data.removeprefix("p2p:deal:dispute:"))
    deal = await session.get(P2PDeal, deal_id)
    if deal is None or deal.status != DealStatus.AWAITING_CONFIRMATION or deal.buyer_id != user.id:
        await callback.answer()
        return
    await state.update_data(deal_id=deal_id)
    await state.set_state(P2PDisputeStates.entering_reason)
    await callback.message.answer(t(user.language, "p2p_dispute_enter_reason"))
    await callback.answer()


@router.message(P2PDisputeStates.entering_reason)
async def on_dispute_reason(message: Message, user: User, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    deal = await session.get(P2PDeal, data.get("deal_id"), options=[selectinload(P2PDeal.listing)])
    await state.clear()
    if deal is None:
        return

    reason = (message.text or "").strip()
    deal.status = DealStatus.DISPUTED
    deal.admin_note = reason
    await session.commit()

    await message.answer(t(user.language, "p2p_dispute_filed"))

    seller = await session.get(User, deal.listing.seller_id)
    from bot.keyboards.p2p import admin_dispute_kb

    for admin_id in settings.admin_id_list:
        try:
            await bot.send_message(
                admin_id,
                t(
                    "ru",
                    "p2p_admin_dispute",
                    deal_id=deal.id,
                    title=deal.listing.title,
                    buyer=_display_name(user),
                    seller=_display_name(seller),
                    amount=fmt_money(deal.escrow_uzs),
                    reason=reason,
                ),
                reply_markup=admin_dispute_kb("ru", deal.id),
            )
        except Exception:
            pass


@router.callback_query(F.data == "p2p:mydeals")
async def on_my_deals(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    lang = user.language
    result = await session.execute(
        select(P2PDeal)
        .join(Listing, P2PDeal.listing_id == Listing.id)
        .where((P2PDeal.buyer_id == user.id) | (Listing.seller_id == user.id))
        .options(selectinload(P2PDeal.listing))
        .order_by(P2PDeal.id.desc())
        .limit(20)
    )
    deals = result.scalars().all()
    if not deals:
        await callback.message.answer(t(lang, "p2p_my_deals_empty"))
        await callback.answer()
        return

    lines = []
    for deal in deals:
        role = "buyer" if deal.buyer_id == user.id else "seller"
        lines.append(t(lang, "p2p_deal_item", id=deal.id, title=deal.listing.title, price=fmt_money(deal.escrow_uzs), status=deal.status, role=role))
    await callback.message.answer("\n\n".join(lines))
    await callback.answer()
