from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main import main_menu_kb
from bot.locales import LOCALES, t
from bot.states import TopupStates
from db.models import CardTopupRequest, TxStatus, User

router = Router(name="start")

TEXT_TO_MENU_KEY: dict[str, str] = {}
for _lang_dict in LOCALES.values():
    for _key in ("menu_market", "menu_wallet", "menu_rent", "menu_p2p", "menu_profile", "menu_admin"):
        TEXT_TO_MENU_KEY[_lang_dict[_key]] = _key


@router.message(CommandStart())
async def cmd_start(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()

    payload = message.text.split(maxsplit=1)[1].strip() if message.text and " " in message.text else ""

    if payload.startswith("topup_"):
        request_id = payload.removeprefix("topup_")
        req = await session.get(CardTopupRequest, int(request_id)) if request_id.isdigit() else None
        if req and req.user_id == user.id and req.status == TxStatus.PENDING and not req.receipt_file_id:
            await state.set_state(TopupStates.waiting_receipt)
            await state.update_data(request_id=req.id)
            await message.answer(t(user.language, "send_receipt"))
            return

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
