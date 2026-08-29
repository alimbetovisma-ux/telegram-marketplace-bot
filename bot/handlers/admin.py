from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.admin import admin_add_item_category_kb, admin_menu_kb
from bot.keyboards.catalog import admin_order_kb
from bot.keyboards.wallet import admin_topup_review_kb
from bot.locales import t
from bot.services import credit_balance, fmt_money
from bot.states import AdminAddItemStates
from db.models import CardTopupRequest, CatalogItem, Order, OrderStatus, TxStatus, User

router = Router(name="admin")

ADMIN_LANG = "ru"


def is_admin(user: User) -> bool:
    return user.tg_id in settings.admin_id_list


async def show_admin_menu(message: Message, user: User) -> None:
    if not is_admin(user):
        await message.answer(t(user.language, "admin_no_access"))
        return
    await message.answer(t(ADMIN_LANG, "admin_menu_title"), reply_markup=admin_menu_kb(ADMIN_LANG))


@router.callback_query(F.data == "admin:menu:topups")
async def on_pending_topups(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    if not is_admin(user):
        await callback.answer(t(user.language, "admin_no_access"), show_alert=True)
        return
    result = await session.execute(
        select(CardTopupRequest).where(CardTopupRequest.status == TxStatus.PENDING).order_by(CardTopupRequest.id)
    )
    reqs = result.scalars().all()
    await callback.answer()
    if not reqs:
        await callback.message.answer(t(ADMIN_LANG, "admin_no_pending_topups"))
        return
    for req in reqs:
        buyer = await session.get(User, req.user_id)
        buyer_name = f"@{buyer.username}" if buyer and buyer.username else str(buyer.tg_id if buyer else req.user_id)
        caption = t(ADMIN_LANG, "topup_pending_admin", user=buyer_name, amount=fmt_money(req.amount_uzs), request_id=req.id)
        kb = admin_topup_review_kb(ADMIN_LANG, req.id)
        if req.receipt_file_id:
            await callback.message.answer_photo(req.receipt_file_id, caption=caption, reply_markup=kb)
        else:
            await callback.message.answer(caption, reply_markup=kb)


@router.callback_query(F.data == "admin:menu:orders")
async def on_pending_orders(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    if not is_admin(user):
        await callback.answer(t(user.language, "admin_no_access"), show_alert=True)
        return
    result = await session.execute(
        select(Order)
        .where(Order.status == OrderStatus.PAID_AWAITING_FULFILLMENT)
        .options(selectinload(Order.item))
        .order_by(Order.id)
    )
    orders = result.scalars().all()
    await callback.answer()
    if not orders:
        await callback.message.answer(t(ADMIN_LANG, "admin_no_pending_orders"))
        return
    for order in orders:
        buyer = await session.get(User, order.user_id)
        buyer_name = f"@{buyer.username}" if buyer and buyer.username else str(buyer.tg_id if buyer else order.user_id)
        text = t(ADMIN_LANG, "admin_new_order_notify", user=buyer_name, title=order.item.title, total=fmt_money(order.total_uzs), order_id=order.id)
        await callback.message.answer(text, reply_markup=admin_order_kb(ADMIN_LANG, order.id))


@router.callback_query(F.data.startswith("admin:topup:"))
async def on_topup_review(callback: CallbackQuery, user: User, session: AsyncSession, bot: Bot) -> None:
    if not is_admin(user):
        await callback.answer(t(user.language, "admin_no_access"), show_alert=True)
        return
    _, _, action, req_id_str = callback.data.split(":")
    req = await session.get(CardTopupRequest, int(req_id_str))
    if req is None or req.status != TxStatus.PENDING:
        await callback.answer(t(ADMIN_LANG, "already_reviewed"), show_alert=True)
        return

    buyer = await session.get(User, req.user_id)
    req.admin_id = user.tg_id
    req.reviewed_at = datetime.now(timezone.utc)

    if action == "approve":
        req.status = TxStatus.CONFIRMED
        await credit_balance(session, buyer, req.amount_uzs, "topup_card", meta={"request_id": req.id})
        await session.commit()
        try:
            await bot.send_message(buyer.tg_id, t(buyer.language, "topup_confirmed", amount=fmt_money(req.amount_uzs), balance=fmt_money(buyer.balance)))
        except Exception:
            pass
    else:
        req.status = TxStatus.REJECTED
        await session.commit()
        try:
            await bot.send_message(buyer.tg_id, t(buyer.language, "topup_rejected"))
        except Exception:
            pass

    if callback.message.caption is not None:
        await callback.message.edit_caption(caption=f"{callback.message.caption}\n\n— {req.status}")
    else:
        await callback.message.edit_text(f"{callback.message.text}\n\n— {req.status}")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:order:fulfill:"))
async def on_order_fulfill(callback: CallbackQuery, user: User, session: AsyncSession, bot: Bot) -> None:
    if not is_admin(user):
        await callback.answer(t(user.language, "admin_no_access"), show_alert=True)
        return
    order_id = int(callback.data.removeprefix("admin:order:fulfill:"))
    order = await session.get(Order, order_id)
    if order is None or order.status != OrderStatus.PAID_AWAITING_FULFILLMENT:
        await callback.answer(t(ADMIN_LANG, "already_reviewed"), show_alert=True)
        return

    order.status = OrderStatus.FULFILLED
    order.fulfilled_by_admin_id = user.tg_id
    order.fulfilled_at = datetime.now(timezone.utc)
    await session.commit()

    buyer = await session.get(User, order.user_id)
    try:
        await bot.send_message(buyer.tg_id, t(buyer.language, "order_fulfilled_notify", order_id=order.id))
    except Exception:
        pass

    await callback.message.edit_text(f"{callback.message.text}\n\n✅ {order.status}")
    await callback.answer()


@router.callback_query(F.data == "admin:menu:add_item")
async def on_add_item_start(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    if not is_admin(user):
        await callback.answer(t(user.language, "admin_no_access"), show_alert=True)
        return
    await state.set_state(AdminAddItemStates.choosing_category)
    await callback.message.answer(t(ADMIN_LANG, "admin_add_item_category"), reply_markup=admin_add_item_category_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:additem:cat:"))
async def on_add_item_category(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    if not is_admin(user):
        await callback.answer(t(user.language, "admin_no_access"), show_alert=True)
        return
    category = callback.data.removeprefix("admin:additem:cat:")
    await state.update_data(category=category)
    await state.set_state(AdminAddItemStates.entering_title)
    await callback.message.answer(t(ADMIN_LANG, "admin_add_item_title"))
    await callback.answer()


@router.message(AdminAddItemStates.entering_title)
async def on_add_item_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(AdminAddItemStates.entering_price)
    await message.answer(t(ADMIN_LANG, "admin_add_item_price"))


@router.message(AdminAddItemStates.entering_price)
async def on_add_item_price(message: Message, state: FSMContext) -> None:
    try:
        price = Decimal((message.text or "").strip().replace(" ", "").replace(",", ""))
    except InvalidOperation:
        await message.answer(t(ADMIN_LANG, "invalid_amount"))
        return
    await state.update_data(price=str(price))
    await state.set_state(AdminAddItemStates.entering_description)
    await message.answer(t(ADMIN_LANG, "admin_add_item_description"))


@router.message(AdminAddItemStates.entering_description)
async def on_add_item_description(message: Message, state: FSMContext) -> None:
    description = None if (message.text or "").strip() == "/skip" else (message.text or "").strip()
    await state.update_data(description=description)
    await state.set_state(AdminAddItemStates.entering_photo)
    await message.answer(t(ADMIN_LANG, "admin_add_item_photo"))


@router.message(AdminAddItemStates.entering_photo)
async def on_add_item_photo(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    image_url = None
    if message.photo:
        image_url = message.photo[-1].file_id
    elif (message.text or "").strip() != "/skip":
        await message.answer(t(ADMIN_LANG, "admin_add_item_photo"))
        return

    data = await state.get_data()
    item = CatalogItem(
        category=data["category"],
        title=data["title"],
        description=data.get("description"),
        price_uzs=Decimal(data["price"]),
        image_url=image_url,
        active=True,
        created_by_admin_id=user.tg_id,
    )
    session.add(item)
    await session.commit()
    await state.clear()
    await message.answer(t(ADMIN_LANG, "admin_add_item_done", title=item.title))
