from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CatalogItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    title: str
    description: str | None
    price_uzs: Decimal
    image_url: str | None
    tags: list | None
    discount_percent: int
    stock: int | None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    catalog_item_id: int
    item_title: str
    qty: int
    total_uzs: Decimal
    status: str
    created_at: datetime


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    amount_uzs: Decimal
    currency: str
    status: str
    created_at: datetime


class MeOut(BaseModel):
    id: int
    tg_id: int
    username: str | None
    first_name: str | None
    language: str
    balance: Decimal
    referral_code: str
    referral_link: str


class CardTopupRequestIn(BaseModel):
    amount_uzs: Decimal


class CardTopupRequestOut(BaseModel):
    request_id: int
    amount_uzs: Decimal
    card_number: str
    card_holder: str
    bot_deeplink: str


class StarsTopupIn(BaseModel):
    amount_uzs: Decimal


class StarsTopupOut(BaseModel):
    stars: int
    invoice_link: str


class LanguageIn(BaseModel):
    language: str
