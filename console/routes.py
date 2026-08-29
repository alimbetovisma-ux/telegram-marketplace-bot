import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from console.auth import SESSION_COOKIE, create_session_token, oauth, require_console_admin
from db.models import CatalogItem, Category
from db.session import get_session

router = APIRouter(prefix="/console")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.filters["tojson"] = lambda value: json.dumps(value, ensure_ascii=False)

GIFT_CATEGORIES = (Category.GIFT_NEW, Category.GIFT_OLD, Category.RENT_NFT)

CATEGORY_LABELS = {
    Category.PREMIUM: "Premium",
    Category.STARS: "Stars",
    Category.GIFT_NEW: "Подарки (новые)",
    Category.GIFT_OLD: "Подарки (редкие)",
    Category.RENT_NUMBER: "Аренда номера",
    Category.RENT_USERNAME: "Аренда username",
    Category.RENT_NFT: "Аренда NFT",
}
templates.env.globals["category_labels"] = CATEGORY_LABELS


# ---- auth ----


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"console_enabled": settings.console_enabled})


@router.get("/auth/google")
async def auth_google(request: Request):
    redirect_uri = f"{settings.public_url}/console/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo") or {}
    email = (userinfo.get("email") or "").lower()

    if not email or not userinfo.get("email_verified") or email not in settings.console_admin_email_list:
        return HTMLResponse("Доступ запрещён — этот Google-аккаунт не в списке разрешённых.", status_code=403)

    session_token = create_session_token(email)
    response = RedirectResponse(url="/console", status_code=302)
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        httponly=True,
        secure=settings.public_url.startswith("https://"),
        samesite="lax",
        max_age=7 * 86400,
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/console/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE)
    return response


# ---- dashboard ----


@router.get("", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    email: Annotated[str, Depends(require_console_admin)],
):
    total_items = (
        await session.execute(select(func.count(CatalogItem.id)).where(CatalogItem.active.is_(True)))
    ).scalar_one()
    total_gifts = (
        await session.execute(
            select(func.count(CatalogItem.id)).where(
                CatalogItem.category.in_(GIFT_CATEGORIES), CatalogItem.active.is_(True)
            )
        )
    ).scalar_one()
    return templates.TemplateResponse(
        request, "dashboard.html", {"total_items": total_items, "total_gifts": total_gifts, "email": email}
    )


# ---- catalog (products & prices) ----


@router.get("/catalog", response_class=HTMLResponse)
async def catalog_page(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    email: Annotated[str, Depends(require_console_admin)],
):
    result = await session.execute(select(CatalogItem).order_by(CatalogItem.id.desc()))
    items = result.scalars().all()
    return templates.TemplateResponse(request, "catalog.html", {"items": items, "email": email})


@router.get("/catalog/new", response_class=HTMLResponse)
async def catalog_new_page(request: Request, email: Annotated[str, Depends(require_console_admin)]):
    return templates.TemplateResponse(
        request, "catalog_form.html", {"item": None, "categories": Category.ALL, "email": email}
    )


@router.get("/catalog/{item_id}/edit", response_class=HTMLResponse)
async def catalog_edit_page(
    item_id: int,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    email: Annotated[str, Depends(require_console_admin)],
):
    item = await session.get(CatalogItem, item_id)
    return templates.TemplateResponse(
        request, "catalog_form.html", {"item": item, "categories": Category.ALL, "email": email}
    )


def _parse_catalog_form(form: dict) -> dict:
    stock_raw = (form.get("stock") or "").strip()
    duration_raw = (form.get("duration_options") or "").strip()

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
        "duration_options": duration_options,
        "active": form.get("active") == "on",
    }


@router.post("/catalog/new")
async def catalog_create(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    _email: Annotated[str, Depends(require_console_admin)],
):
    form = dict(await request.form())
    try:
        data = _parse_catalog_form(form)
    except (KeyError, InvalidOperation):
        return RedirectResponse(url="/console/catalog/new", status_code=303)
    item = CatalogItem(**data)
    session.add(item)
    await session.commit()
    return RedirectResponse(url="/console/catalog?ok=1", status_code=303)


@router.post("/catalog/{item_id}/edit")
async def catalog_update(
    item_id: int,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    _email: Annotated[str, Depends(require_console_admin)],
):
    item = await session.get(CatalogItem, item_id)
    if item is None:
        return RedirectResponse(url="/console/catalog", status_code=303)
    form = dict(await request.form())
    try:
        data = _parse_catalog_form(form)
    except (KeyError, InvalidOperation):
        return RedirectResponse(url=f"/console/catalog/{item_id}/edit", status_code=303)
    for key, value in data.items():
        setattr(item, key, value)
    await session.commit()
    return RedirectResponse(url="/console/catalog?ok=1", status_code=303)


# ---- NFT gifts ----


@router.get("/gifts", response_class=HTMLResponse)
async def gifts_page(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    email: Annotated[str, Depends(require_console_admin)],
):
    result = await session.execute(
        select(CatalogItem).where(CatalogItem.category.in_(GIFT_CATEGORIES)).order_by(CatalogItem.id.desc())
    )
    gifts = result.scalars().all()
    return templates.TemplateResponse(request, "gifts.html", {"gifts": gifts, "email": email})


@router.post("/gifts/new")
async def gifts_create(
    session: Annotated[AsyncSession, Depends(get_session)],
    _email: Annotated[str, Depends(require_console_admin)],
    title: Annotated[str, Form()],
    price_uzs: Annotated[str, Form()],
    category: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    image_url: Annotated[str, Form()] = "",
):
    try:
        price = Decimal(price_uzs)
    except InvalidOperation:
        return RedirectResponse(url="/console/gifts", status_code=303)
    if category not in GIFT_CATEGORIES:
        category = Category.GIFT_NEW
    item = CatalogItem(
        category=category,
        title=title.strip(),
        description=description.strip() or None,
        price_uzs=price,
        image_url=image_url.strip() or None,
        active=True,
    )
    session.add(item)
    await session.commit()
    return RedirectResponse(url="/console/gifts?ok=1", status_code=303)


@router.post("/gifts/{item_id}/toggle-active")
async def gifts_toggle_active(
    item_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    _email: Annotated[str, Depends(require_console_admin)],
):
    item = await session.get(CatalogItem, item_id)
    if item is not None:
        item.active = not item.active
        await session.commit()
    return RedirectResponse(url="/console/gifts?ok=1", status_code=303)
