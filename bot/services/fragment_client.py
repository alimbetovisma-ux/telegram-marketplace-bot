"""Thin wrapper around `pyfragment` (https://pypi.org/project/pyfragment/) for
buying Telegram Premium / Stars directly through fragment.com, paid from the
bot's own TON wallet.

pyfragment needs two things that don't come from the code itself:

1. The same TON wallet mnemonic as ton_wallet.py (`settings.ton_wallet_mnemonic`)
   -- pyfragment signs and broadcasts the payment itself, it does not reuse
   our ton_wallet.py module.
2. Fragment session cookies (`stel_ssid`, `stel_dt`, `stel_token`,
   `stel_ton_token`) from a real fragment.com login. Obtain them once by
   logging into fragment.com in a browser with a Telegram account that has a
   TON wallet connected, then copying those four cookies from devtools
   (Application -> Cookies) into `.env`. They expire periodically and need
   to be refreshed by repeating this.

NOTE: not executed/tested locally (no Python runtime available in the
environment that wrote this). `fulfillment.py` only calls this with a
try/except + timeout and always falls back to manual admin fulfillment on
any failure, so a bug here degrades to "slower delivery", not lost money.
"""

from __future__ import annotations

from dataclasses import dataclass

from pyfragment import FragmentClient, FragmentError

from bot.config import settings


class FragmentNotConfigured(Exception):
    pass


@dataclass
class FragmentResult:
    transaction_id: str
    username: str
    amount: int


def _client() -> FragmentClient:
    if not settings.fragment_enabled:
        raise FragmentNotConfigured("Fragment cookies or TON wallet are not configured")
    return FragmentClient(
        seed=settings.ton_wallet_mnemonic,
        api_key=settings.ton_api_key,
        cookies={
            "stel_ssid": settings.fragment_stel_ssid,
            "stel_dt": settings.fragment_stel_dt,
            "stel_token": settings.fragment_stel_token,
            "stel_ton_token": settings.fragment_stel_ton_token,
        },
    )


async def buy_premium(username: str, months: int) -> FragmentResult:
    async with _client() as client:
        result = await client.purchase_premium(username, months=months)
        return FragmentResult(transaction_id=result.transaction_id, username=result.username, amount=result.amount)


async def buy_stars(username: str, amount: int) -> FragmentResult:
    async with _client() as client:
        result = await client.purchase_stars(username, amount=amount)
        return FragmentResult(transaction_id=result.transaction_id, username=result.username, amount=result.amount)


__all__ = ["FragmentResult", "FragmentNotConfigured", "FragmentError", "buy_premium", "buy_stars"]
