"""Google OAuth2 login for the /console site (separate from the Telegram-based /admin panel)."""

from __future__ import annotations

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from bot.config import settings

SESSION_COOKIE = "console_session"
_MAX_SESSION_AGE = 7 * 86400

_serializer = URLSafeTimedSerializer(settings.console_session_secret)

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def create_session_token(email: str) -> str:
    return _serializer.dumps({"email": email})


def read_session_email(token: str | None) -> str | None:
    if not token:
        return None
    try:
        data = _serializer.loads(token, max_age=_MAX_SESSION_AGE)
    except BadSignature:
        return None
    return data.get("email")


async def require_console_admin(request: Request) -> str:
    email = read_session_email(request.cookies.get(SESSION_COOKIE))
    if email is None or email not in settings.console_admin_email_list:
        raise HTTPException(status_code=303, headers={"Location": "/console/login"})
    return email
