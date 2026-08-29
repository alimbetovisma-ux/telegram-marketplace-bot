from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy import select

from db.models import User
from db.session import SessionLocal


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        async with SessionLocal() as session:
            user = None
            if tg_user is not None:
                result = await session.execute(select(User).where(User.tg_id == tg_user.id))
                user = result.scalar_one_or_none()
                if user is None:
                    user = User(
                        tg_id=tg_user.id,
                        username=tg_user.username,
                        first_name=tg_user.first_name,
                        language=(tg_user.language_code or "uz") if tg_user.language_code in ("uz", "ru", "en") else "uz",
                    )
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                elif user.username != tg_user.username or user.first_name != tg_user.first_name:
                    user.username = tg_user.username
                    user.first_name = tg_user.first_name
                    await session.commit()

            data["session"] = session
            data["user"] = user
            return await handler(event, data)
