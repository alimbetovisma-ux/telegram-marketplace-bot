from __future__ import annotations

import secrets
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


def gen_referral_code() -> str:
    return secrets.token_urlsafe(6)


def gen_ton_memo() -> str:
    return f"D-{secrets.token_hex(4).upper()}"


class TxType:
    TOPUP_CARD = "topup_card"
    TOPUP_STARS = "topup_stars"
    TOPUP_CRYPTO = "topup_crypto"
    SELL_CRYPTO = "sell_crypto"
    PURCHASE = "purchase"
    RENT = "rent"
    REFERRAL_BONUS = "referral_bonus"
    ADMIN_ADJUST = "admin_adjust"
    REFUND = "refund"
    P2P_ESCROW = "p2p_escrow"
    P2P_RELEASE = "p2p_release"
    P2P_REFUND = "p2p_refund"


class TxStatus:
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class Category:
    PREMIUM = "premium"
    STARS = "stars"
    GIFT_NEW = "gift_new"
    GIFT_OLD = "gift_old"
    RENT_NUMBER = "rent_number"
    RENT_USERNAME = "rent_username"
    RENT_NFT = "rent_nft"

    ALL = (PREMIUM, STARS, GIFT_NEW, GIFT_OLD, RENT_NUMBER, RENT_USERNAME, RENT_NFT)
    RENTAL = (RENT_NUMBER, RENT_USERNAME, RENT_NFT)


class OrderStatus:
    PAID_AWAITING_FULFILLMENT = "paid_awaiting_fulfillment"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class RentalAssetStatus:
    AVAILABLE = "available"
    RENTED = "rented"
    RETIRED = "retired"


class ListingType:
    NFT_GIFT = "nft_gift"
    USERNAME = "username"

    ALL = (NFT_GIFT, USERNAME)


class ListingStatus:
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    RESERVED = "reserved"
    SOLD = "sold"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DealStatus:
    AWAITING_TRANSFER = "awaiting_transfer"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    REFUNDED = "refunded"


class TonDirection:
    TOPUP = "topup"
    SELL = "sell"


class TonRequestStatus:
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="uz")
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    referral_code: Mapped[str] = mapped_column(String(16), unique=True, default=gen_referral_code)
    referred_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")
    orders: Mapped[list["Order"]] = relationship(back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(8), default="UZS")
    amount_uzs: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(16), default=TxStatus.PENDING)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="transactions")


class CardTopupRequest(Base):
    __tablename__ = "card_topup_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"), nullable=True)
    amount_uzs: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    receipt_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default=TxStatus.PENDING)
    admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CatalogItem(Base):
    __tablename__ = "catalog_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_uzs: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    duration_options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    discount_percent: Mapped[int] = mapped_column(Integer, default=0)
    stock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    catalog_item_id: Mapped[int] = mapped_column(ForeignKey("catalog_items.id"))
    qty: Mapped[int] = mapped_column(Integer, default=1)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_uzs: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(32), default=OrderStatus.PAID_AWAITING_FULFILLMENT)
    target_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fulfillment_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    fulfilled_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="orders")
    item: Mapped["CatalogItem"] = relationship()


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class RentalAsset(Base):
    __tablename__ = "rental_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    catalog_item_id: Mapped[int] = mapped_column(ForeignKey("catalog_items.id"), index=True)
    category: Mapped[str] = mapped_column(String(32))
    access_payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default=RentalAssetStatus.AVAILABLE)
    current_order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    rented_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    item: Mapped["CatalogItem"] = relationship()


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    price_uzs: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(16), default=ListingStatus.PENDING_REVIEW)
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    seller: Mapped["User"] = relationship()


class P2PDeal(Base):
    __tablename__ = "p2p_deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    escrow_uzs: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    commission_uzs: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(24), default=DealStatus.AWAITING_TRANSFER)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    listing: Mapped["Listing"] = relationship()
    buyer: Mapped["User"] = relationship()


class TonTopupRequest(Base):
    __tablename__ = "ton_topup_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    direction: Mapped[str] = mapped_column(String(8), default=TonDirection.TOPUP)
    currency: Mapped[str] = mapped_column(String(8))
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(20, 9))
    memo: Mapped[str] = mapped_column(String(32), unique=True, default=gen_ton_memo)
    status: Mapped[str] = mapped_column(String(16), default=TonRequestStatus.PENDING)
    tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    credited_uzs: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
