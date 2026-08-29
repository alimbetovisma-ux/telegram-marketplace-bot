"""Sending side of the bot's TON hot wallet.

Built on `tonutils` (https://github.com/nessshon/tonutils, v2.2.0 API).
Reading/monitoring incoming transactions lives in ton_monitor.py instead --
it talks to the TonAPI REST API directly, which returns already-decoded
JSON (amount, sender, comment) instead of raw TL-B cells.

NOTE: this module could not be executed/tested in the environment that
wrote it (no Python runtime available there). Before relying on it with
real funds, do a small mainnet-or-testnet dry run: send a tiny amount out
via send_ton() and confirm it lands, using a wallet funded with a
throwaway amount.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from ton_core import Address, NetworkGlobalID, to_nano
from tonutils.clients import ToncenterClient
from tonutils.contracts import JettonTransferBuilder, WalletV4R2

from bot.config import settings

# USD₮ (Tether) jetton master contract on TON mainnet.
DEFAULT_USDT_MASTER = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"

_NETWORK = NetworkGlobalID.MAINNET if settings.ton_network == "mainnet" else NetworkGlobalID.TESTNET


class TonWalletError(Exception):
    pass


class TonNotConfigured(TonWalletError):
    pass


def _require_configured() -> None:
    if not settings.ton_enabled:
        raise TonNotConfigured("TON_WALLET_MNEMONIC is not set")


def _make_client() -> ToncenterClient:
    kwargs: dict = {"network": _NETWORK}
    if settings.ton_api_key:
        kwargs["api_key"] = settings.ton_api_key
    return ToncenterClient(**kwargs)


async def get_wallet_address() -> str:
    """Return the hot wallet's user-friendly address (does not require network access)."""
    _require_configured()
    client = _make_client()
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, settings.ton_wallet_mnemonic)
    return wallet.address.to_str(is_bounceable=False)


async def get_balance_ton() -> Decimal:
    _require_configured()
    client = _make_client()
    async with client:
        wallet, _, _, _ = WalletV4R2.from_mnemonic(client, settings.ton_wallet_mnemonic)
        await wallet.refresh()
        return Decimal(wallet.balance) / Decimal(10**9)


async def send_ton(destination: str, amount_ton: Decimal, comment: str = "") -> str:
    """Send native TON. Returns the normalized message hash."""
    _require_configured()
    client = _make_client()
    async with client:
        wallet, _, _, _ = WalletV4R2.from_mnemonic(client, settings.ton_wallet_mnemonic)
        msg = await wallet.transfer(
            destination=Address(destination),
            amount=to_nano(float(amount_ton)),
            body=comment or None,
        )
        return msg.normalized_hash


async def send_usdt(destination: str, amount_usdt: Decimal, comment: str = "", jetton_master: str | None = None) -> str:
    """Send USD₮ (jetton, 6 decimals). Returns the normalized message hash.

    The wallet needs both a USD₮ jetton balance AND a small TON balance to
    cover gas for the jetton transfer (~0.05 TON per send).
    """
    _require_configured()
    client = _make_client()
    async with client:
        wallet, _, _, _ = WalletV4R2.from_mnemonic(client, settings.ton_wallet_mnemonic)
        msg = await wallet.transfer_message(
            JettonTransferBuilder(
                destination=Address(destination),
                jetton_amount=to_nano(float(amount_usdt), decimals=6),
                jetton_master_address=Address(jetton_master or DEFAULT_USDT_MASTER),
                forward_payload=comment or None,
                forward_amount=1,
                amount=to_nano(0.05),
            )
        )
        return msg.normalized_hash


def get_wallet_address_sync() -> str:
    """Convenience sync wrapper for use in non-async admin scripts."""
    return asyncio.run(get_wallet_address())
