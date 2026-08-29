from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.locales import t
from db.models import ListingType

TYPE_LABEL_KEY = {ListingType.NFT_GIFT: "p2p_type_nft_gift", ListingType.USERNAME: "p2p_type_username"}


def p2p_menu_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_p2p_browse"), callback_data="p2p:browse")],
            [InlineKeyboardButton(text=t(lang, "btn_p2p_sell"), callback_data="p2p:sell")],
            [InlineKeyboardButton(text=t(lang, "btn_p2p_my_deals"), callback_data="p2p:mydeals")],
        ]
    )


def p2p_type_kb(lang: str, prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, TYPE_LABEL_KEY[tp]), callback_data=f"{prefix}:{tp}")]
            for tp in ListingType.ALL
        ]
    )


def listing_list_kb(listings: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=title, callback_data=f"p2p:view:{lid}")] for lid, title in listings]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def listing_detail_kb(lang: str, listing_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t(lang, "btn_p2p_buy"), callback_data=f"p2p:buy:{listing_id}")]]
    )


def admin_listing_review_kb(listing_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅", callback_data=f"admin:listing:approve:{listing_id}"),
                InlineKeyboardButton(text="❌", callback_data=f"admin:listing:reject:{listing_id}"),
            ]
        ]
    )


def seller_sent_kb(lang: str, deal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t(lang, "btn_p2p_sent"), callback_data=f"p2p:deal:sent:{deal_id}")]]
    )


def buyer_confirm_kb(lang: str, deal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_p2p_confirm"), callback_data=f"p2p:deal:confirm:{deal_id}")],
            [InlineKeyboardButton(text=t(lang, "btn_p2p_dispute"), callback_data=f"p2p:deal:dispute:{deal_id}")],
        ]
    )


def admin_dispute_kb(lang: str, deal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_p2p_release"), callback_data=f"admin:deal:release:{deal_id}")],
            [InlineKeyboardButton(text=t(lang, "btn_p2p_refund"), callback_data=f"admin:deal:refund:{deal_id}")],
        ]
    )
