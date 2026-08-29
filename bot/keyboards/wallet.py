from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import settings
from bot.locales import t


def wallet_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_topup"), callback_data="wallet:topup")],
            [
                InlineKeyboardButton(text=t(lang, "btn_history"), callback_data="wallet:history"),
                InlineKeyboardButton(text=t(lang, "btn_my_orders"), callback_data="wallet:orders"),
            ],
        ]
    )


def topup_method_kb(lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(lang, "btn_topup_card"), callback_data="topup:method:card")],
        [InlineKeyboardButton(text=t(lang, "btn_topup_stars"), callback_data="topup:method:stars")],
    ]
    if settings.ton_enabled:
        rows.append([InlineKeyboardButton(text=t(lang, "btn_topup_crypto"), callback_data="topup:method:crypto")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def crypto_currency_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="TON", callback_data="topup:crypto:cur:TON"),
                InlineKeyboardButton(text="USDT", callback_data="topup:crypto:cur:USDT"),
            ]
        ]
    )


def crypto_direction_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_crypto_topup"), callback_data="topup:crypto:dir:topup")],
            [
                InlineKeyboardButton(
                    text=t(lang, "btn_crypto_sell", percent=settings.p2p_commission_percent),
                    callback_data="topup:crypto:dir:sell",
                )
            ],
        ]
    )


def i_paid_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t(lang, "btn_i_paid"), callback_data="topup:card:paid")]]
    )


def admin_topup_review_kb(lang: str, request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_approve"), callback_data=f"admin:topup:approve:{request_id}"),
                InlineKeyboardButton(text=t(lang, "btn_reject"), callback_data=f"admin:topup:reject:{request_id}"),
            ]
        ]
    )
