from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin import show_admin_menu
from bot.handlers.catalog import show_market, show_rent
from bot.handlers.profile import show_profile
from bot.handlers.start import TEXT_TO_MENU_KEY
from bot.handlers.wallet import show_wallet
from db.models import User

router = Router(name="menu")


@router.message(F.text.in_(TEXT_TO_MENU_KEY.keys()))
async def on_menu_button(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    key = TEXT_TO_MENU_KEY[message.text]
    if key == "menu_market":
        await show_market(message, user)
    elif key == "menu_wallet":
        await show_wallet(message, user)
    elif key == "menu_rent":
        await show_rent(message, user)
    elif key == "menu_profile":
        await show_profile(message, user)
    elif key == "menu_admin":
        await show_admin_menu(message, user)
