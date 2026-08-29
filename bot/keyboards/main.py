from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from bot.config import settings
from bot.locales import t


def main_menu_kb(lang: str, tg_id: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🚀 Mini App", web_app=WebAppInfo(url=settings.web_app_url))],
        [KeyboardButton(text=t(lang, "menu_market")), KeyboardButton(text=t(lang, "menu_wallet"))],
        [KeyboardButton(text=t(lang, "menu_rent")), KeyboardButton(text=t(lang, "menu_p2p"))],
        [KeyboardButton(text=t(lang, "menu_profile"))],
    ]
    if tg_id in settings.admin_id_list:
        rows.append([KeyboardButton(text=t(lang, "menu_admin"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
