import hashlib
import hmac
import json
from typing import Annotated
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from db.models import User
from db.session import get_session


def validate_init_data(init_data: str) -> dict | None:
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, received_hash):
        return None
    return parsed


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    authorization: Annotated[str | None, Header()] = None,
    x_telegram_init_data: Annotated[str | None, Header()] = None,
) -> User:
    init_data = x_telegram_init_data
    if not init_data and authorization and authorization.lower().startswith("tma "):
        init_data = authorization[4:]

    if not init_data:
        raise HTTPException(status_code=401, detail="Missing Telegram init data")

    parsed = validate_init_data(init_data)
    if parsed is None:
        raise HTTPException(status_code=401, detail="Invalid Telegram init data")

    try:
        tg_user = json.loads(parsed.get("user", "{}"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=401, detail="Invalid user payload")

    tg_id = tg_user.get("id")
    if not tg_id:
        raise HTTPException(status_code=401, detail="No user id in init data")

    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if user is None:
        lang = tg_user.get("language_code")
        user = User(
            tg_id=tg_id,
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name"),
            language=lang if lang in ("uz", "ru", "en") else "uz",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Account blocked")
    return user
