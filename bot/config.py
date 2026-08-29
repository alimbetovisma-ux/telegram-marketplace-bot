from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str
    admin_ids: str = ""
    webhook_secret: str = "dev-secret"
    public_url: str = "http://localhost:8000"
    web_app_url: str = "http://localhost:8000/app"

    database_url: str = "postgresql+asyncpg://botuser:botpass@localhost:5432/botdb"

    card_number: str = "0000 0000 0000 0000"
    card_holder: str = "Card Holder"
    stars_to_uzs_rate: Decimal = Decimal("200")
    referral_bonus_percent: Decimal = Decimal("5")
    p2p_commission_percent: Decimal = Decimal("3")

    # TON hot wallet (Stage 2). Empty mnemonic = TON/Fragment features stay disabled.
    ton_wallet_mnemonic: str = ""
    ton_api_key: str = ""
    ton_network: str = "mainnet"
    ton_rate_uzs: Decimal = Decimal("0")
    usdt_rate_uzs: Decimal = Decimal("0")
    ton_monitor_interval_seconds: int = 20
    ton_request_ttl_minutes: int = 60

    # Fragment (fragment.com) session cookies -- see README for how to obtain them.
    # Empty = Fragment auto-buy stays disabled and orders fall back to manual admin fulfillment.
    fragment_stel_ssid: str = ""
    fragment_stel_dt: str = ""
    fragment_stel_token: str = ""
    fragment_stel_ton_token: str = ""
    fragment_timeout_seconds: int = 120

    # Web admin panel session signing key -- set a random string in production.
    admin_session_secret: str = "dev-admin-secret-change-me"

    @property
    def admin_id_list(self) -> list[int]:
        return [int(x) for x in self.admin_ids.split(",") if x.strip()]

    @property
    def webhook_path(self) -> str:
        return f"/webhook/{self.webhook_secret}"

    @property
    def ton_enabled(self) -> bool:
        return bool(self.ton_wallet_mnemonic.strip())

    @property
    def fragment_enabled(self) -> bool:
        return bool(self.fragment_stel_token.strip() and self.ton_enabled)


settings = Settings()
