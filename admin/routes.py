import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from admin.auth import SESSION_COOKIE, create_session_token, require_admin, verify_telegram_login
from bot.bot_instance import bot
from bot.config import settings
from bot.locales import t
import bot.runtime as runtime
from bot.services import credit_balance, fmt_money, get_setting, set_setting
from db.models import (
    CardTopupRequest,
    CatalogItem,
    Category,
    DealStatus,
    Listing,
    ListingStatus,
    Order,
    OrderStatus,
    P2PDeal,
    RentalAsset,
    RentalAssetStatus,
    Transaction,
    TxStatus,
    TxType,
    User,
)
from db.session import get_session

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.filters["tojson"] = lambda value: json.dumps(value, ensure_ascii=False)


def _user_label(user: User | None, fallback_id: int | None = None) -> str:
    if user is None:
        return str(fallback_id or "-")
    return f"@{user.username}" if user.username else (user.first_name or str(user.tg_id))


# ---- auth ----


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    auth_url = f"{settings.public_url}/admin/auth"
    return templates.TemplateResponse(request, "login.html", {"bot_username": runtime.bot_username, "auth_url": auth_url})


@router.get("/auth")
async def auth_callback(request: Request):
    data = dict(request.query_params)
    if not verify_telegram_login(data) or int(data.get("id", 0)) not in settings.admin_id_list:
        return HTMLResponse("Access denied", status_code=403)

    token = create_session_token(int(data["id"]))
    response = RedirectResponse(url="/admin", status_code=302)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, secure=settings.public_url.startswith("https://"), samesite="lax", max_age=7 * 86400)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE)
    return response


# ---- dashboard ----


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    async def count(stmt) -> int:
        result = await session.execute(select(func.count()).select_from(stmt.subquery()))
        return result.scalar_one()

    stats = {
        "pending_topups": await count(select(CardTopupRequest.id).where(CardTopupRequest.status == TxStatus.PENDING)),
        "pending_orders": await count(select(Order.id).where(Order.status == OrderStatus.PAID_AWAITING_FULFILLMENT)),
        "pending_listings": await count(select(Listing.id).where(Listing.status == ListingStatus.PENDING_REVIEW)),
        "disputed_deals": await count(select(P2PDeal.id).where(P2PDeal.status == DealStatus.DISPUTED)),
        "catalog_items": await count(select(CatalogItem.id).where(CatalogItem.active.is_(True))),
        "available_assets": await count(select(RentalAsset.id).where(RentalAsset.status == RentalAssetStatus.AVAILABLE)),
        "total_users": await count(select(User.id)),
    }
    return templates.TemplateResponse(
        request, "dashboard.html", {"stats": stats, "ton_enabled": settings.ton_enabled, "fragment_enabled": settings.fragment_enabled}
    )


# ---- card top-ups ----


@router.get("/topups", response_class=HTMLResponse)
async def topups_page(request: Request, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    result = await session.execute(select(CardTopupRequest).order_by(CardTopupRequest.id.desc()).limit(100))
    reqs = result.scalars().all()
    rows = []
    for r in reqs:
        user = await session.get(User, r.user_id)
        rows.append({"id": r.id, "user_label": _user_label(user), "amount_uzs": fmt_money(r.amount_uzs), "status": r.status, "receipt_file_id": r.receipt_file_id})
    return templates.TemplateResponse(request, "topups.html", {"requests": rows})


@router.post("/topups/{request_id}/approve")
async def topup_approve(request_id: int, session: Annotated[AsyncSession, Depends(get_session)], admin_id: Annotated[int, Depends(require_admin)]):
    req = await session.get(CardTopupRequest, request_id)
    if req and req.status == TxStatus.PENDING:
        user = await session.get(User, req.user_id)
        req.status = TxStatus.CONFIRMED
        req.admin_id = admin_id
        req.reviewed_at = datetime.now(timezone.utc)
        await credit_balance(session, user, req.amount_uzs, TxType.TOPUP_CARD, meta={"request_id": req.id, "via": "web_admin"})
        await session.commit()
        try:
            await bot.send_message(user.tg_id, t(user.language, "topup_confirmed", amount=fmt_money(req.amount_uzs), balance=fmt_money(user.balance)))
        except Exception:
            pass
    return RedirectResponse(url="/admin/topups?ok=1", status_code=303)


@router.post("/topups/{request_id}/reject")
async def topup_reject(request_id: int, session: Annotated[AsyncSession, Depends(get_session)], admin_id: Annotated[int, Depends(require_admin)]):
    req = await session.get(CardTopupRequest, request_id)
    if req and req.status == TxStatus.PENDING:
        user = await session.get(User, req.user_id)
        req.status = TxStatus.REJECTED
        req.admin_id = admin_id
        req.reviewed_at = datetime.now(timezone.utc)
        await session.commit()
        try:
            await bot.send_message(user.tg_id, t(user.language, "topup_rejected"))
        except Exception:
            pass
    return RedirectResponse(url="/admin/topups?ok=1", status_code=303)


# ---- orders ----


@router.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    result = await session.execute(select(Order).options(selectinload(Order.item)).order_by(Order.id.desc()).limit(100))
    orders = result.scalars().all()
    rows = []
    for o in orders:
        user = await session.get(User, o.user_id)
        rows.append({"id": o.id, "user_label": _user_label(user), "item_title": o.item.title, "total_uzs": fmt_money(o.total_uzs), "status": o.status, "fulfillment_note": o.fulfillment_note})
    return templates.TemplateResponse(request, "orders.html", {"orders": rows})


@router.post("/orders/{order_id}/fulfill")
async def order_fulfill(order_id: int, session: Annotated[AsyncSession, Depends(get_session)], admin_id: Annotated[int, Depends(require_admin)]):
    order = await session.get(Order, order_id)
    if order and order.status == OrderStatus.PAID_AWAITING_FULFILLMENT:
        order.status = OrderStatus.FULFILLED
        order.fulfilled_by_admin_id = admin_id
        order.fulfilled_at = datetime.now(timezone.utc)
        await session.commit()
        user = await session.get(User, order.user_id)
        try:
            await bot.send_message(user.tg_id, t(user.language, "order_fulfilled_notify", order_id=order.id))
        except Exception:
            pass
    return RedirectResponse(url="/admin/orders?ok=1", status_code=303)


# ---- catalog ----


@router.get("/catalog", response_class=HTMLResponse)
async def catalog_page(request: Request, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    result = await session.execute(select(CatalogItem).order_by(CatalogItem.id.desc()))
    items = result.scalars().all()
    return templates.TemplateResponse(request, "catalog.html", {"items": items})


@router.get("/catalog/new", response_class=HTMLResponse)
async def catalog_new_page(request: Request, _admin: Annotated[int, Depends(require_admin)]):
    return templates.TemplateResponse(request, "catalog_form.html", {"item": None, "categories": Category.ALL})


@router.get("/catalog/{item_id}/edit", response_class=HTMLResponse)
async def catalog_edit_page(item_id: int, request: Request, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    item = await session.get(CatalogItem, item_id)
    return templates.TemplateResponse(request, "catalog_form.html", {"item": item, "categories": Category.ALL})


def _parse_catalog_form(form: dict) -> dict:
    stock_raw = (form.get("stock") or "").strip()
    duration_raw = (form.get("duration_options") or "").strip()
    tags_raw = (form.get("tags") or "").strip()

    duration_options = None
    if duration_raw:
        try:
            duration_options = json.loads(duration_raw)
        except json.JSONDecodeError:
            duration_options = None

    return {
        "category": form["category"],
        "title": form["title"].strip(),
        "description": (form.get("description") or "").strip() or None,
        "price_uzs": Decimal(form["price_uzs"]),
        "discount_percent": int(form.get("discount_percent") or 0),
        "stock": int(stock_raw) if stock_raw else None,
        "image_url": (form.get("image_url") or "").strip() or None,
        "tags": [x.strip() for x in tags_raw.split(",") if x.strip()] or None,
        "duration_options": duration_options,
        "active": form.get("active") == "on",
    }


@router.post("/catalog/new")
async def catalog_create(request: Request, session: Annotated[AsyncSession, Depends(get_session)], admin_id: Annotated[int, Depends(require_admin)]):
    form = dict((await request.form()))
    try:
        data = _parse_catalog_form(form)
    except (KeyError, InvalidOperation):
        return RedirectResponse(url="/admin/catalog/new", status_code=303)
    item = CatalogItem(created_by_admin_id=admin_id, **data)
    session.add(item)
    await session.commit()
    return RedirectResponse(url="/admin/catalog?ok=1", status_code=303)


@router.post("/catalog/{item_id}/edit")
async def catalog_update(item_id: int, request: Request, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    item = await session.get(CatalogItem, item_id)
    if item is None:
        return RedirectResponse(url="/admin/catalog", status_code=303)
    form = dict((await request.form()))
    try:
        data = _parse_catalog_form(form)
    except (KeyError, InvalidOperation):
        return RedirectResponse(url=f"/admin/catalog/{item_id}/edit", status_code=303)
    for key, value in data.items():
        setattr(item, key, value)
    await session.commit()
    return RedirectResponse(url="/admin/catalog?ok=1", status_code=303)


# ---- rental assets ----


@router.get("/assets", response_class=HTMLResponse)
async def assets_page(request: Request, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    result = await session.execute(select(RentalAsset).options(selectinload(RentalAsset.item)).order_by(RentalAsset.id.desc()).limit(200))
    assets = result.scalars().all()
    rows = [{"id": a.id, "item_title": a.item.title, "status": a.status, "rented_until": a.rented_until, "current_order_id": a.current_order_id} for a in assets]

    result = await session.execute(select(CatalogItem).where(CatalogItem.category.in_(Category.RENTAL), CatalogItem.active.is_(True)).order_by(CatalogItem.id.desc()))
    rental_items = result.scalars().all()
    return templates.TemplateResponse(request, "assets.html", {"assets": rows, "rental_items": rental_items})


@router.post("/assets/new")
async def assets_create(
    session: Annotated[AsyncSession, Depends(get_session)],
    admin_id: Annotated[int, Depends(require_admin)],
    catalog_item_id: Annotated[int, Form()],
    access_payload: Annotated[str, Form()],
):
    item = await session.get(CatalogItem, catalog_item_id)
    if item is not None and access_payload.strip():
        asset = RentalAsset(catalog_item_id=item.id, category=item.category, access_payload=access_payload.strip(), created_by_admin_id=admin_id)
        session.add(asset)
        await session.commit()
    return RedirectResponse(url="/admin/assets?ok=1", status_code=303)


# ---- P2P listings ----


@router.get("/listings", response_class=HTMLResponse)
async def listings_page(request: Request, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    result = await session.execute(select(Listing).order_by(Listing.id.desc()).limit(100))
    listings = result.scalars().all()
    rows = []
    for listing in listings:
        seller = await session.get(User, listing.seller_id)
        rows.append({"id": listing.id, "seller_label": _user_label(seller), "type": listing.type, "title": listing.title, "price_uzs": fmt_money(listing.price_uzs), "status": listing.status})
    return templates.TemplateResponse(request, "listings.html", {"listings": rows})


@router.post("/listings/{listing_id}/approve")
async def listing_approve(listing_id: int, session: Annotated[AsyncSession, Depends(get_session)], admin_id: Annotated[int, Depends(require_admin)]):
    listing = await session.get(Listing, listing_id)
    if listing and listing.status == ListingStatus.PENDING_REVIEW:
        listing.status = ListingStatus.ACTIVE
        listing.reviewed_by_admin_id = admin_id
        await session.commit()
        seller = await session.get(User, listing.seller_id)
        try:
            await bot.send_message(seller.tg_id, t(seller.language, "p2p_listing_approved", title=listing.title))
        except Exception:
            pass
    return RedirectResponse(url="/admin/listings?ok=1", status_code=303)


@router.post("/listings/{listing_id}/reject")
async def listing_reject(listing_id: int, session: Annotated[AsyncSession, Depends(get_session)], admin_id: Annotated[int, Depends(require_admin)]):
    listing = await session.get(Listing, listing_id)
    if listing and listing.status == ListingStatus.PENDING_REVIEW:
        listing.status = ListingStatus.REJECTED
        listing.reviewed_by_admin_id = admin_id
        await session.commit()
        seller = await session.get(User, listing.seller_id)
        try:
            await bot.send_message(seller.tg_id, t(seller.language, "p2p_listing_rejected", title=listing.title))
        except Exception:
            pass
    return RedirectResponse(url="/admin/listings?ok=1", status_code=303)


# ---- P2P deals / disputes ----


@router.get("/deals", response_class=HTMLResponse)
async def deals_page(request: Request, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    result = await session.execute(select(P2PDeal).options(selectinload(P2PDeal.listing)).order_by(P2PDeal.id.desc()).limit(100))
    deals = result.scalars().all()
    rows = []
    for d in deals:
        buyer = await session.get(User, d.buyer_id)
        seller = await session.get(User, d.listing.seller_id)
        rows.append({"id": d.id, "title": d.listing.title, "buyer_label": _user_label(buyer), "seller_label": _user_label(seller), "escrow_uzs": fmt_money(d.escrow_uzs), "status": d.status, "admin_note": d.admin_note})
    return templates.TemplateResponse(request, "deals.html", {"deals": rows})


@router.post("/deals/{deal_id}/release")
async def deal_release(deal_id: int, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    deal = await session.get(P2PDeal, deal_id, options=[selectinload(P2PDeal.listing)])
    if deal and deal.status == DealStatus.DISPUTED:
        deal.status = DealStatus.COMPLETED
        deal.listing.status = ListingStatus.SOLD
        seller = await session.get(User, deal.listing.seller_id)
        buyer = await session.get(User, deal.buyer_id)
        payout = deal.escrow_uzs - deal.commission_uzs
        await credit_balance(session, seller, payout, TxType.P2P_RELEASE, meta={"deal_id": deal.id, "admin_resolved": True})
        await session.commit()
        for u in (seller, buyer):
            try:
                await bot.send_message(u.tg_id, t(u.language, "p2p_dispute_released"))
            except Exception:
                pass
    return RedirectResponse(url="/admin/deals?ok=1", status_code=303)


@router.post("/deals/{deal_id}/refund")
async def deal_refund(deal_id: int, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    deal = await session.get(P2PDeal, deal_id, options=[selectinload(P2PDeal.listing)])
    if deal and deal.status == DealStatus.DISPUTED:
        deal.status = DealStatus.REFUNDED
        deal.listing.status = ListingStatus.ACTIVE
        buyer = await session.get(User, deal.buyer_id)
        seller = await session.get(User, deal.listing.seller_id)
        await credit_balance(session, buyer, deal.escrow_uzs, TxType.P2P_REFUND, meta={"deal_id": deal.id, "admin_resolved": True})
        await session.commit()
        for u in (buyer, seller):
            try:
                await bot.send_message(u.tg_id, t(u.language, "p2p_dispute_refunded"))
            except Exception:
                pass
    return RedirectResponse(url="/admin/deals?ok=1", status_code=303)


# ---- settings ----


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    card_number = await get_setting(session, "card_number", settings.card_number)
    card_holder = await get_setting(session, "card_holder", settings.card_holder)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "card_number": card_number,
            "card_holder": card_holder,
            "ton_enabled": settings.ton_enabled,
            "fragment_enabled": settings.fragment_enabled,
            "ton_rate": settings.ton_rate_uzs,
            "usdt_rate": settings.usdt_rate_uzs,
            "p2p_commission": settings.p2p_commission_percent,
            "stars_rate": settings.stars_to_uzs_rate,
            "referral_percent": settings.referral_bonus_percent,
        },
    )


@router.post("/settings")
async def settings_update(
    session: Annotated[AsyncSession, Depends(get_session)],
    _admin: Annotated[int, Depends(require_admin)],
    card_number: Annotated[str, Form()],
    card_holder: Annotated[str, Form()],
):
    await set_setting(session, "card_number", card_number.strip())
    await set_setting(session, "card_holder", card_holder.strip())
    return RedirectResponse(url="/admin/settings?ok=1", status_code=303)


# ---- users ----

PAGE_SIZE = 50


@router.get("/users", response_class=HTMLResponse)
async def users_page(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    _admin: Annotated[int, Depends(require_admin)],
    q: str = "",
    page: int = 1,
):
    stmt = select(User).order_by(User.id.desc())
    if q.strip():
        like = f"%{q.strip()}%"
        conditions = [User.username.ilike(like), User.first_name.ilike(like)]
        if q.strip().lstrip("-").isdigit():
            conditions.append(User.tg_id == int(q.strip()))
        stmt = stmt.where(or_(*conditions))

    page = max(page, 1)
    result = await session.execute(stmt.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE + 1))
    rows = result.scalars().all()
    has_next = len(rows) > PAGE_SIZE
    rows = rows[:PAGE_SIZE]

    users_out = []
    for u in rows:
        referred_by_label = None
        if u.referred_by_id:
            ref = await session.get(User, u.referred_by_id)
            referred_by_label = _user_label(ref)
        users_out.append(
            {
                "id": u.id,
                "tg_id": u.tg_id,
                "label": _user_label(u),
                "balance": fmt_money(u.balance),
                "referred_by_label": referred_by_label,
                "is_blocked": u.is_blocked,
                "created_at": u.created_at.strftime("%Y-%m-%d %H:%M"),
            }
        )

    return templates.TemplateResponse(request, "users.html", {"users": users_out, "q": q, "page": page, "has_next": has_next})


@router.post("/users/{user_id}/adjust")
async def user_adjust(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    admin_id: Annotated[int, Depends(require_admin)],
    amount: Annotated[str, Form()] = "",
    reason: Annotated[str, Form()] = "",
):
    user = await session.get(User, user_id)
    if user and amount.strip():
        try:
            delta = Decimal(amount.strip())
        except InvalidOperation:
            delta = Decimal("0")
        if delta != 0:
            await credit_balance(session, user, delta, TxType.ADMIN_ADJUST, meta={"admin_id": admin_id, "reason": reason.strip()})
            await session.commit()
    return RedirectResponse(url="/admin/users?ok=1", status_code=303)


@router.post("/users/{user_id}/toggle-block")
async def user_toggle_block(user_id: int, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    user = await session.get(User, user_id)
    if user:
        user.is_blocked = not user.is_blocked
        await session.commit()
    return RedirectResponse(url="/admin/users?ok=1", status_code=303)


# ---- transactions ----


@router.get("/transactions", response_class=HTMLResponse)
async def transactions_page(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    _admin: Annotated[int, Depends(require_admin)],
    q: str = "",
    type: str = "",
    status: str = "",
    page: int = 1,
):
    stmt = select(Transaction).order_by(Transaction.id.desc())
    if type:
        stmt = stmt.where(Transaction.type == type)
    if status:
        stmt = stmt.where(Transaction.status == status)
    if q.strip():
        like = f"%{q.strip()}%"
        conditions = [User.username.ilike(like), User.first_name.ilike(like)]
        if q.strip().lstrip("-").isdigit():
            conditions.append(User.tg_id == int(q.strip()))
        match_result = await session.execute(select(User.id).where(or_(*conditions)))
        matched_ids = [row[0] for row in match_result.all()]
        stmt = stmt.where(Transaction.user_id.in_(matched_ids or [-1]))

    page = max(page, 1)
    result = await session.execute(stmt.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE + 1))
    rows = result.scalars().all()
    has_next = len(rows) > PAGE_SIZE
    rows = rows[:PAGE_SIZE]

    txs_out = []
    for tx in rows:
        user = await session.get(User, tx.user_id)
        txs_out.append(
            {
                "id": tx.id,
                "user_label": _user_label(user, tx.user_id),
                "type": tx.type,
                "amount_uzs": fmt_money(tx.amount_uzs),
                "positive": tx.amount_uzs >= 0,
                "currency": tx.currency,
                "status": tx.status,
                "created_at": tx.created_at.strftime("%Y-%m-%d %H:%M"),
            }
        )

    return templates.TemplateResponse(
        request,
        "transactions.html",
        {
            "txs": txs_out,
            "q": q,
            "page": page,
            "has_next": has_next,
            "type_filter": type,
            "status_filter": status,
            "types": [
                TxType.TOPUP_CARD,
                TxType.TOPUP_STARS,
                TxType.TOPUP_CRYPTO,
                TxType.SELL_CRYPTO,
                TxType.PURCHASE,
                TxType.RENT,
                TxType.REFERRAL_BONUS,
                TxType.ADMIN_ADJUST,
                TxType.REFUND,
                TxType.P2P_ESCROW,
                TxType.P2P_RELEASE,
                TxType.P2P_REFUND,
            ],
            "statuses": [TxStatus.PENDING, TxStatus.CONFIRMED, TxStatus.REJECTED],
        },
    )


# ---- stats ----


@router.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request, session: Annotated[AsyncSession, Depends(get_session)], _admin: Annotated[int, Depends(require_admin)]):
    now = datetime.now(timezone.utc)
    since14 = now - timedelta(days=14)
    since30 = now - timedelta(days=30)

    revenue_result = await session.execute(
        select(func.date_trunc("day", Transaction.created_at), func.sum(func.abs(Transaction.amount_uzs)))
        .where(Transaction.type.in_([TxType.PURCHASE, TxType.RENT]), Transaction.created_at >= since14)
        .group_by(func.date_trunc("day", Transaction.created_at))
    )
    revenue_map = {row[0].date(): float(row[1]) for row in revenue_result.all()}

    users_result = await session.execute(
        select(func.date_trunc("day", User.created_at), func.count())
        .where(User.created_at >= since14)
        .group_by(func.date_trunc("day", User.created_at))
    )
    users_map = {row[0].date(): row[1] for row in users_result.all()}

    today = now.date()
    max_rev = max(revenue_map.values()) if revenue_map else 1
    max_users = max(users_map.values()) if users_map else 1
    revenue_days, users_days = [], []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        rev = revenue_map.get(d, 0)
        cnt = users_map.get(d, 0)
        revenue_days.append({"label": d.strftime("%d.%m"), "short": fmt_money(rev) if rev else "0", "pct": max(int(rev / max_rev * 100), 2) if max_rev else 2})
        users_days.append({"label": d.strftime("%d.%m"), "short": str(cnt), "pct": max(int(cnt / max_users * 100), 2) if max_users else 2})

    top_result = await session.execute(
        select(CatalogItem.title, func.count(Order.id), func.sum(Order.total_uzs))
        .join(Order, Order.catalog_item_id == CatalogItem.id)
        .where(Order.status != OrderStatus.CANCELLED)
        .group_by(CatalogItem.id, CatalogItem.title)
        .order_by(func.count(Order.id).desc())
        .limit(5)
    )
    top_items = [{"title": row[0], "count": row[1], "revenue": fmt_money(row[2] or 0)} for row in top_result.all()]

    revenue_30d = (await session.execute(
        select(func.sum(func.abs(Transaction.amount_uzs))).where(Transaction.type.in_([TxType.PURCHASE, TxType.RENT]), Transaction.created_at >= since30)
    )).scalar_one() or 0
    orders_30d = (await session.execute(select(func.count(Order.id)).where(Order.created_at >= since30))).scalar_one()
    new_users_30d = (await session.execute(select(func.count(User.id)).where(User.created_at >= since30))).scalar_one()
    total_balance = (await session.execute(select(func.sum(User.balance)))).scalar_one() or 0

    totals = {
        "revenue_30d": fmt_money(revenue_30d),
        "orders_30d": orders_30d,
        "new_users_30d": new_users_30d,
        "total_balance": fmt_money(total_balance),
    }

    return templates.TemplateResponse(
        request, "stats.html", {"revenue_days": revenue_days, "users_days": users_days, "top_items": top_items, "totals": totals}
    )
