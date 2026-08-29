from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.models import Category
from bot.locales import t


def admin_menu_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "admin_pending_topups"), callback_data="admin:menu:topups")],
            [InlineKeyboardButton(text=t(lang, "admin_pending_orders"), callback_data="admin:menu:orders")],
            [InlineKeyboardButton(text=t(lang, "admin_add_item"), callback_data="admin:menu:add_item")],
        ]
    )


def admin_add_item_category_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=c, callback_data=f"admin:additem:cat:{c}")] for c in Category.ALL]
    return InlineKeyboardMarkup(inline_keyboard=rows)
