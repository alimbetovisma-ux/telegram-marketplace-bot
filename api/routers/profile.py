from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.schemas import LanguageIn, MeOut
from bot.runtime import bot_username
from db.models import User
from db.session import get_session

router = APIRouter(prefix="/api/me", tags=["profile"])

VALID_LANGUAGES = {"uz", "ru", "en"}


def _ref_link(user: User) -> str:
    return f"https://t.me/{bot_username or 'your_bot'}?start=ref_{user.referral_code}"


@router.get("", response_model=MeOut)
async def get_me(user: Annotated[User, Depends(get_current_user)]) -> MeOut:
    return MeOut(
        id=user.id,
        tg_id=user.tg_id,
        username=user.username,
        first_name=user.first_name,
        language=user.language,
        balance=user.balance,
        referral_code=user.referral_code,
        referral_link=_ref_link(user),
    )


@router.post("/language", response_model=MeOut)
async def set_language(
    payload: LanguageIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> MeOut:
    if payload.language not in VALID_LANGUAGES:
        raise HTTPException(status_code=400, detail="Unsupported language")
    user.language = payload.language
    await session.commit()
    return MeOut(
        id=user.id,
        tg_id=user.tg_id,
        username=user.username,
        first_name=user.first_name,
        language=user.language,
        balance=user.balance,
        referral_code=user.referral_code,
        referral_link=_ref_link(user),
    )
