from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.schemas import CatalogItemOut
from db.models import CatalogItem, Category, User
from db.session import get_session

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("", response_model=list[CatalogItemOut])
async def list_catalog(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
    category: Annotated[str | None, Query()] = None,
) -> list[CatalogItem]:
    if category and category not in Category.ALL:
        raise HTTPException(status_code=400, detail="Unknown category")
    stmt = select(CatalogItem).where(CatalogItem.active.is_(True)).order_by(CatalogItem.id.desc())
    if category:
        stmt = stmt.where(CatalogItem.category == category)
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{item_id}", response_model=CatalogItemOut)
async def get_catalog_item(
    item_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
) -> CatalogItem:
    item = await session.get(CatalogItem, item_id)
    if item is None or not item.active:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
