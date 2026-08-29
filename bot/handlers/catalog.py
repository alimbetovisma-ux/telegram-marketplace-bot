from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.catalog import (
    MARKET_CATEGORIES,
    RENT_CATEGORIES,
    categories_kb,
    item_detail_kb,
    items_list_kb,
)
from bot.locales import t
from bot.services import fmt_money, purchase_item
from db.models import CatalogItem, User

router = Router(name="catalog")


async def show_market(message: Message, user: User) -> None:
    await message.answer(t(user.language, "market_title"), reply_markup=categories_kb(user.language, MARKET_CATEGORIES))


async def show_rent(message: Message, user: User) -> None:
    await message.answer(t(user.language, "rent_title"), reply_markup=categories_kb(user.language, RENT_CATEGORIES))


@router.callback_query(F.data.startswith("cat:"))
async def on_category(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    category = callback.data.removeprefix("cat:")
    result = await session.execute(
        select(CatalogItem).where(CatalogItem.category == category, CatalogItem.active.is_(True)).order_by(CatalogItem.id.desc())
    )
    items = result.scalars().all()
    lang = user.language
    if not items:
        await callback.message.edit_text(t(lang, "category_empty"), reply_markup=categories_kb(lang, MARKET_CATEGORIES if category in MARKET_CATEGORIES else RENT_CATEGORIES))
        await callback.answer()
        return

    pairs = [(i.id, f"{i.title} — {fmt_money(i.price_uzs)} so'm") for i in items]
    await callback.message.edit_text(t(lang, "market_title" if category in MARKET_CATEGORIES else "rent_title"), reply_markup=items_list_kb(lang, category, pairs))
    await callback.answer()


@router.callback_query(F.data.startswith("item:"))
async def on_item(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    item_id = int(callback.data.removeprefix("item:"))
    item = await session.get(CatalogItem, item_id)
    lang = user.language
    if item is None or not item.active:
        await callback.answer(t(lang, "category_empty"), show_alert=True)
        return

    discount = f" (-{item.discount_percent}%)" if item.discount_percent else ""
    text = t(lang, "item_card", title=item.title, description=item.description or "", price=fmt_money(item.price_uzs), discount=discount)
    kb = item_detail_kb(lang, item.id, item.category, fmt_money(item.price_uzs))

    await callback.message.delete()
    if item.image_url:
        await callback.message.answer_photo(item.image_url, caption=text, reply_markup=kb)
    else:
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def on_buy(callback: CallbackQuery, user: User, session: AsyncSession, bot: Bot) -> None:
    item_id = int(callback.data.removeprefix("buy:"))
    item = await session.get(CatalogItem, item_id)
    lang = user.language
    if item is None or not item.active:
        await callback.answer(t(lang, "category_empty"), show_alert=True)
        return

    price = item.price_uzs
    if user.balance < price:
        await callback.answer(t(lang, "insufficient_balance", price=fmt_money(price), balance=fmt_money(user.balance)), show_alert=True)
        return

    order, bonus_info = await purchase_item(session, user, item)
    await session.commit()
    await session.refresh(order)

    await callback.message.answer(t(lang, "purchase_success", order_id=order.id, title=item.title, total=fmt_money(price)))
    await callback.answer()

    if bonus_info:
        referrer, bonus = bonus_info
        try:
            await bot.send_message(referrer.tg_id, t(referrer.language, "referral_bonus_earned", amount=fmt_money(bonus)))
        except Exception:
            pass

    buyer_name = f"@{user.username}" if user.username else (user.first_name or str(user.tg_id))
    for admin_id in settings.admin_id_list:
        try:
            await bot.send_message(
                admin_id,
                t("ru", "admin_new_order_notify", user=buyer_name, title=item.title, total=fmt_money(price), order_id=order.id),
            )
        except Exception:
            pass


@router.callback_query(F.data == "back:main")
async def on_back_main(callback: CallbackQuery, user: User) -> None:
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "back:market")
async def on_back_market(callback: CallbackQuery, user: User) -> None:
    await callback.message.edit_text(t(user.language, "market_title"), reply_markup=categories_kb(user.language, MARKET_CATEGORIES))
    await callback.answer()


@router.callback_query(F.data == "back:rent")
async def on_back_rent(callback: CallbackQuery, user: User) -> None:
    await callback.message.edit_text(t(user.language, "rent_title"), reply_markup=categories_kb(user.language, RENT_CATEGORIES))
    await callback.answer()
