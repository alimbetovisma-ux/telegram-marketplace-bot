from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from db.models import CardTopupRequest, CatalogItem, Category, Order, Setting, Transaction, TxStatus, TxType, User


class InsufficientBalance(Exception):
    pass


class ItemUnavailable(Exception):
    pass


def fmt_money(value: Decimal | int | float) -> str:
    value = Decimal(value)
    q = value.quantize(Decimal("1"))
    return f"{q:,.0f}".replace(",", " ")


async def get_setting(session: AsyncSession, key: str, default: str) -> str:
    result = await session.execute(select(Setting).where(Setting.key == key))
    row = result.scalar_one_or_none()
    return row.value if row else default


async def set_setting(session: AsyncSession, key: str, value: str) -> None:
    result = await session.execute(select(Setting).where(Setting.key == key))
    row = result.scalar_one_or_none()
    if row:
        row.value = value
    else:
        session.add(Setting(key=key, value=value))
    await session.commit()


async def credit_balance(
    session: AsyncSession,
    user: User,
    amount_uzs: Decimal,
    tx_type: str,
    currency: str = "UZS",
    meta: dict | None = None,
) -> Transaction:
    """Apply a signed balance delta and record it. Caller commits."""
    user.balance = user.balance + amount_uzs
    tx = Transaction(
        user_id=user.id,
        type=tx_type,
        currency=currency,
        amount_uzs=amount_uzs,
        status=TxStatus.CONFIRMED,
        meta=meta or {},
    )
    session.add(tx)
    return tx


async def apply_referral_bonus(session: AsyncSession, buyer: User, purchase_amount: Decimal) -> tuple[User, Decimal] | None:
    if not buyer.referred_by_id:
        return None
    result = await session.execute(select(User).where(User.id == buyer.referred_by_id))
    referrer = result.scalar_one_or_none()
    if referrer is None:
        return None
    bonus = (purchase_amount * settings.referral_bonus_percent / Decimal("100")).quantize(Decimal("1"))
    if bonus <= 0:
        return None
    await credit_balance(session, referrer, bonus, "referral_bonus", meta={"from_user_id": buyer.id})
    return referrer, bonus


async def purchase_item(session: AsyncSession, user: User, item: CatalogItem) -> tuple[Order, tuple[User, Decimal] | None]:
    """Debit the buyer, create the order, and apply any referral bonus.

    Raises ItemUnavailable / InsufficientBalance instead of touching the DB
    when the purchase can't go through. Caller commits.
    """
    if not item.active or (item.stock is not None and item.stock <= 0):
        raise ItemUnavailable()
    if user.balance < item.price_uzs:
        raise InsufficientBalance()

    price = item.price_uzs
    order = Order(user_id=user.id, catalog_item_id=item.id, qty=1, total_uzs=price)
    session.add(order)

    tx_type = TxType.RENT if item.category in Category.RENTAL else TxType.PURCHASE
    await credit_balance(session, user, -price, tx_type, meta={"catalog_item_id": item.id})

    if item.stock is not None and item.stock > 0:
        item.stock -= 1
        if item.stock == 0:
            item.active = False

    bonus_info = await apply_referral_bonus(session, user, price)
    return order, bonus_info


async def create_card_topup_request(session: AsyncSession, user: User, amount_uzs: Decimal) -> CardTopupRequest:
    tx = Transaction(user_id=user.id, type=TxType.TOPUP_CARD, currency="UZS", amount_uzs=amount_uzs, status=TxStatus.PENDING)
    session.add(tx)
    await session.flush()
    req = CardTopupRequest(user_id=user.id, transaction_id=tx.id, amount_uzs=amount_uzs, status=TxStatus.PENDING)
    session.add(req)
    return req
