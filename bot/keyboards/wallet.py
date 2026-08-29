from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_topup_card"), callback_data="topup:method:card")],
            [InlineKeyboardButton(text=t(lang, "btn_topup_stars"), callback_data="topup:method:stars")],
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
