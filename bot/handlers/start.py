from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main import main_menu_kb
from bot.locales import LOCALES, t
from db.models import User

router = Router(name="start")

TEXT_TO_MENU_KEY: dict[str, str] = {}
for _lang_dict in LOCALES.values():
    for _key in ("menu_market", "menu_wallet", "menu_rent", "menu_p2p", "menu_profile", "menu_admin"):
        TEXT_TO_MENU_KEY[_lang_dict[_key]] = _key


@router.message(CommandStart())
async def cmd_start(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()

    payload = message.text.split(maxsplit=1)[1].strip() if message.text and " " in message.text else ""
    if payload.startswith("ref_") and user.referred_by_id is None:
        code = payload.removeprefix("ref_")
        result = await session.execute(select(User).where(User.referral_code == code))
        referrer = result.scalar_one_or_none()
        if referrer and referrer.id != user.id:
            user.referred_by_id = referrer.id
            await session.commit()

    name = user.first_name or "friend"
    await message.answer(t(user.language, "welcome", name=name))
    await message.answer(t(user.language, "welcome_sub"), reply_markup=main_menu_kb(user.language, user.tg_id))
