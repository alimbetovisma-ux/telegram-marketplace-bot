from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.main import main_menu_kb
from bot.keyboards.profile import profile_kb
from bot.locales import t
from bot.runtime import bot_username
from bot.services import fmt_money
from db.models import User

router = Router(name="profile")


def _ref_link(user: User) -> str:
    username = bot_username or "your_bot"
    return f"https://t.me/{username}?start=ref_{user.referral_code}"


async def show_profile(message: Message, user: User) -> None:
    lang = user.language
    name = user.first_name or str(user.tg_id)
    username = user.username or "-"
    text = (
        f"{t(lang, 'profile_title', name=name, username=username)}\n\n"
        f"{t(lang, 'profile_balance', balance=fmt_money(user.balance))}\n\n"
        f"{t(lang, 'profile_referral_title')}\n"
        f"{t(lang, 'profile_referral_desc', percent=settings.referral_bonus_percent)}"
    )
    await message.answer(text, reply_markup=profile_kb(lang))


@router.callback_query(F.data.startswith("lang:"))
async def on_lang(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    code = callback.data.removeprefix("lang:")
    user.language = code
    await session.commit()
    await callback.answer(t(code, "language_changed"))
    await callback.message.answer(t(code, "language_changed"), reply_markup=main_menu_kb(code, user.tg_id))


@router.callback_query(F.data == "profile:ref")
async def on_ref(callback: CallbackQuery, user: User) -> None:
    await callback.message.answer(f"<code>{_ref_link(user)}</code>")
    await callback.answer()
