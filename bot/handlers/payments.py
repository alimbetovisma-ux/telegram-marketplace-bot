from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.types import Message, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.locales import t
from bot.services import credit_balance, fmt_money
from db.models import TxType, User

router = Router(name="payments")


@router.pre_checkout_query()
async def on_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(lambda m: m.successful_payment is not None)
async def on_successful_payment(message: Message, user: User, session: AsyncSession) -> None:
    sp = message.successful_payment
    lang = user.language
    amount_uzs = Decimal("0")
    if sp.invoice_payload.startswith("topup_stars:"):
        try:
            amount_uzs = Decimal(sp.invoice_payload.removeprefix("topup_stars:"))
        except InvalidOperation:
            amount_uzs = Decimal(sp.total_amount) * 0  # unknown payload, do not guess

    if amount_uzs <= 0:
        return

    await credit_balance(
        session,
        user,
        amount_uzs,
        TxType.TOPUP_STARS,
        currency="XTR",
        meta={"stars": sp.total_amount, "charge_id": sp.telegram_payment_charge_id},
    )
    await session.commit()

    await message.answer(t(lang, "stars_payment_success", amount=fmt_money(amount_uzs), balance=fmt_money(user.balance)))
