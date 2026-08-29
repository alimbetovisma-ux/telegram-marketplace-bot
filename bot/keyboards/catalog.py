from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.models import Category
from bot.locales import t

MARKET_CATEGORIES = [Category.PREMIUM, Category.STARS, Category.GIFT_NEW, Category.GIFT_OLD]
RENT_CATEGORIES = [Category.RENT_NUMBER, Category.RENT_USERNAME, Category.RENT_NFT]

CATEGORY_LABEL_KEY = {
    Category.PREMIUM: "cat_premium",
    Category.STARS: "cat_stars",
    Category.GIFT_NEW: "cat_gift_new",
    Category.GIFT_OLD: "cat_gift_old",
    Category.RENT_NUMBER: "cat_rent_number",
    Category.RENT_USERNAME: "cat_rent_username",
    Category.RENT_NFT: "cat_rent_nft",
}


def categories_kb(lang: str, categories: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=t(lang, CATEGORY_LABEL_KEY[c]), callback_data=f"cat:{c}")] for c in categories]
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def items_list_kb(lang: str, category: str, items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=title, callback_data=f"item:{item_id}")] for item_id, title in items]
    back_target = "back:rent" if category in RENT_CATEGORIES else "back:market"
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=back_target)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def item_detail_kb(lang: str, item_id: int, category: str, price: str) -> InlineKeyboardMarkup:
    btn_key = "btn_rent" if category in RENT_CATEGORIES else "btn_buy"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, btn_key, price=price), callback_data=f"buy:{item_id}")],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"cat:{category}")],
        ]
    )


def admin_order_kb(lang: str, order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t(lang, "btn_mark_fulfilled"), callback_data=f"admin:order:fulfill:{order_id}")]]
    )
