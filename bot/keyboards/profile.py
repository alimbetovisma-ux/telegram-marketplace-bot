from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.locales import t

LANGUAGES = [("uz", "🇺🇿 O'zbek"), ("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English")]


def profile_kb(lang: str) -> InlineKeyboardMarkup:
    lang_row = [InlineKeyboardButton(text=label, callback_data=f"lang:{code}") for code, label in LANGUAGES]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            lang_row,
            [InlineKeyboardButton(text=t(lang, "btn_copy_ref"), callback_data="profile:ref")],
        ]
    )
