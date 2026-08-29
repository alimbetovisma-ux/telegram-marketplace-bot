from decimal import Decimal, InvalidOperation

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.wallet import (
    admin_topup_review_kb,
    crypto_currency_kb,
    crypto_direction_kb,
    i_paid_kb,
    topup_method_kb,
    wallet_kb,
)
from bot.locales import t
from bot.services import create_card_topup_request, create_ton_topup_request, fmt_money, get_setting
from bot.services import ton_wallet
from bot.states import TopupStates
from db.models import CardTopupRequest, Order, TonDirection, Transaction, TxStatus, TxType, User

router = Router(name="wallet")


async def show_wallet(message: Message, user: User) -> None:
    lang = user.language
    text = f"{t(lang, 'wallet_title')}\n\n{t(lang, 'balance_label')}\n{fmt_money(user.balance)} so'm"
    await message.answer(text, reply_markup=wallet_kb(lang))


@router.callback_query(F.data == "wallet:topup")
async def on_topup(callback: CallbackQuery, user: User) -> None:
    await callback.message.edit_text(t(user.language, "topup_choose_method"), reply_markup=topup_method_kb(user.language))
    await callback.answer()


@router.callback_query(F.data == "topup:method:card")
async def on_topup_card(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.set_state(TopupStates.entering_amount_card)
    await callback.message.edit_text(t(user.language, "enter_amount"))
    await callback.answer()


@router.callback_query(F.data == "topup:method:stars")
async def on_topup_stars(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.set_state(TopupStates.entering_amount_stars)
    await callback.message.edit_text(t(user.language, "enter_amount"))
    await callback.answer()


@router.callback_query(F.data == "topup:method:crypto")
async def on_topup_crypto(callback: CallbackQuery, user: User) -> None:
    if not settings.ton_enabled:
        await callback.answer(t(user.language, "topup_crypto_disabled"), show_alert=True)
        return
    await callback.message.edit_text(t(user.language, "topup_crypto_choose_currency"), reply_markup=crypto_currency_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("topup:crypto:cur:"))
async def on_topup_crypto_currency(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    currency = callback.data.removeprefix("topup:crypto:cur:")
    await state.update_data(crypto_currency=currency)
    await state.set_state(TopupStates.entering_amount_crypto)
    await callback.message.edit_text(t(user.language, "topup_crypto_enter_amount", currency=currency))
    await callback.answer()


@router.message(TopupStates.entering_amount_crypto)
async def on_amount_crypto(message: Message, user: User, state: FSMContext) -> None:
    lang = user.language
    amount = _parse_amount(message.text or "")
    if amount is None:
        await message.answer(t(lang, "invalid_amount"))
        return
    await state.update_data(crypto_amount=str(amount))
    await message.answer(t(lang, "topup_crypto_choose_direction"), reply_markup=crypto_direction_kb(lang))


@router.callback_query(F.data.startswith("topup:crypto:dir:"))
async def on_topup_crypto_direction(callback: CallbackQuery, user: User, session: AsyncSession, state: FSMContext) -> None:
    lang = user.language
    direction = callback.data.removeprefix("topup:crypto:dir:")
    data = await state.get_data()
    currency = data.get("crypto_currency")
    amount_str = data.get("crypto_amount")
    if not currency or not amount_str:
        await callback.answer()
        return

    amount = Decimal(amount_str)
    req = await create_ton_topup_request(
        session, user, currency, amount, direction=TonDirection.SELL if direction == "sell" else TonDirection.TOPUP
    )
    await session.commit()
    await state.clear()

    try:
        address = await ton_wallet.get_wallet_address()
    except Exception:
        address = "—"

    await callback.message.edit_text(
        t(lang, "topup_crypto_instructions", amount=amount, currency=currency, address=address, memo=req.memo)
    )
    await callback.answer()


def _parse_amount(text: str) -> Decimal | None:
    cleaned = text.strip().replace(" ", "").replace(",", "")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None
    if value <= 0:
        return None
    return value


@router.message(TopupStates.entering_amount_card)
async def on_amount_card(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    lang = user.language
    amount = _parse_amount(message.text or "")
    if amount is None:
        await message.answer(t(lang, "invalid_amount"))
        return

    req = await create_card_topup_request(session, user, amount)
    await session.commit()
    await session.refresh(req)

    await state.update_data(request_id=req.id)
    card_number = await get_setting(session, "card_number", settings.card_number)
    card_holder = await get_setting(session, "card_holder", settings.card_holder)
    await message.answer(
        t(lang, "card_requisites", amount=fmt_money(amount), card_number=card_number, card_holder=card_holder),
        reply_markup=i_paid_kb(lang),
    )


@router.callback_query(F.data == "topup:card:paid")
async def on_card_paid(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("request_id"):
        await callback.answer()
        return
    await state.set_state(TopupStates.waiting_receipt)
    await callback.message.answer(t(user.language, "send_receipt"))
    await callback.answer()


async def _attach_receipt(req: CardTopupRequest, message: Message, user: User, session: AsyncSession, bot: Bot) -> None:
    req.receipt_file_id = message.photo[-1].file_id
    await session.commit()

    await message.answer(t(user.language, "receipt_saved"))

    buyer_name = f"@{user.username}" if user.username else (user.first_name or str(user.tg_id))
    for admin_id in settings.admin_id_list:
        try:
            await bot.send_photo(
                admin_id,
                req.receipt_file_id,
                caption=t("ru", "topup_pending_admin", user=buyer_name, amount=fmt_money(req.amount_uzs), request_id=req.id),
                reply_markup=admin_topup_review_kb("ru", req.id),
            )
        except Exception:
            pass


@router.message(TopupStates.waiting_receipt, F.photo)
async def on_receipt_photo(message: Message, user: User, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    request_id = data.get("request_id")
    req = await session.get(CardTopupRequest, request_id) if request_id else None
    await state.clear()
    if req is None:
        return
    await _attach_receipt(req, message, user, session, bot)


@router.message(StateFilter(None), F.photo)
async def on_receipt_photo_fallback(message: Message, user: User, session: AsyncSession, bot: Bot) -> None:
    """Catches receipt photos when no FSM state matched (e.g. topup started from the Mini App
    and the /start deep link with the request id was skipped or lost by the Telegram client)."""
    result = await session.execute(
        select(CardTopupRequest)
        .where(
            CardTopupRequest.user_id == user.id,
            CardTopupRequest.status == TxStatus.PENDING,
            CardTopupRequest.receipt_file_id.is_(None),
        )
        .order_by(CardTopupRequest.id.desc())
    )
    req = result.scalars().first()
    if req is None:
        return
    await _attach_receipt(req, message, user, session, bot)


@router.message(TopupStates.entering_amount_stars)
async def on_amount_stars(message: Message, user: User, state: FSMContext, bot: Bot) -> None:
    lang = user.language
    amount = _parse_amount(message.text or "")
    if amount is None:
        await message.answer(t(lang, "invalid_amount"))
        return

    stars = int((amount / settings.stars_to_uzs_rate).to_integral_value(rounding="ROUND_CEILING"))
    if stars < 1:
        stars = 1
    await state.clear()

    await bot.send_invoice(
        chat_id=message.chat.id,
        title=t(lang, "stars_invoice_title"),
        description=t(lang, "stars_invoice_desc", stars=stars, amount=fmt_money(amount)),
        payload=f"topup_stars:{amount}",
        currency="XTR",
        prices=[LabeledPrice(label=t(lang, "stars_invoice_title"), amount=stars)],
        provider_token="",
    )


@router.callback_query(F.data == "wallet:history")
async def on_history(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    lang = user.language
    result = await session.execute(
        select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.id.desc()).limit(20)
    )
    txs = result.scalars().all()
    if not txs:
        await callback.message.answer(t(lang, "history_empty"))
        await callback.answer()
        return

    icons = {
        TxType.TOPUP_CARD: "💳",
        TxType.TOPUP_STARS: "⭐️",
        TxType.TOPUP_CRYPTO: "💠",
        TxType.SELL_CRYPTO: "💠",
        TxType.PURCHASE: "🛒",
        TxType.RENT: "🔑",
        TxType.REFERRAL_BONUS: "🎁",
        TxType.ADMIN_ADJUST: "⚙️",
        TxType.REFUND: "↩️",
        TxType.P2P_ESCROW: "🤝",
        TxType.P2P_RELEASE: "🤝",
        TxType.P2P_REFUND: "↩️",
    }
    lines = [
        t(lang, "history_item", icon=icons.get(tx.type, "•"), type=tx.type, amount=fmt_money(tx.amount_uzs), status=tx.status, date=tx.created_at.strftime("%Y-%m-%d %H:%M"))
        for tx in txs
    ]
    await callback.message.answer(f"{t(lang, 'history_title')}\n\n" + "\n\n".join(lines))
    await callback.answer()


@router.callback_query(F.data == "wallet:orders")
async def on_orders(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    lang = user.language
    result = await session.execute(
        select(Order).where(Order.user_id == user.id).options(selectinload(Order.item)).order_by(Order.id.desc()).limit(20)
    )
    orders = result.scalars().all()
    if not orders:
        await callback.message.answer(t(lang, "orders_empty"))
        await callback.answer()
        return

    lines = [t(lang, "order_item", id=o.id, title=o.item.title if o.item else "-", total=fmt_money(o.total_uzs), status=o.status) for o in orders]
    await callback.message.answer("\n\n".join(lines))
    await callback.answer()
