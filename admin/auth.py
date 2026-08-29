"""Telegram Login Widget verification (https://core.telegram.org/widgets/login)
plus a signed session cookie for the web admin panel."""

from __future__ import annotations

import hashlib
import hmac
import time

from fastapi import HTTPException, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from bot.config import settings

SESSION_COOKIE = "admin_session"
_MAX_AUTH_AGE = 86400  # Telegram auth_date freshness window, seconds
_MAX_SESSION_AGE = 7 * 86400

_serializer = URLSafeTimedSerializer(settings.admin_session_secret)


def verify_telegram_login(data: dict) -> bool:
    payload = dict(data)
    received_hash = payload.pop("hash", None)
    if not received_hash:
        return False

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(payload.items()) if v is not None)
    secret_key = hashlib.sha256(settings.bot_token.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, received_hash):
        return False

    try:
        auth_date = int(payload.get("auth_date", 0))
    except (TypeError, ValueError):
        return False
    return time.time() - auth_date <= _MAX_AUTH_AGE


def create_session_token(tg_id: int) -> str:
    return _serializer.dumps({"tg_id": tg_id})


def read_session_token(token: str | None) -> int | None:
    if not token:
        return None
    try:
        data = _serializer.loads(token, max_age=_MAX_SESSION_AGE)
    except BadSignature:
        return None
    tg_id = data.get("tg_id")
    return int(tg_id) if tg_id is not None else None


async def require_admin(request: Request) -> int:
    tg_id = read_session_token(request.cookies.get(SESSION_COOKIE))
    if tg_id is None or tg_id not in settings.admin_id_list:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    return tg_id
