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

    @property
    def admin_id_list(self) -> list[int]:
        return [int(x) for x in self.admin_ids.split(",") if x.strip()]

    @property
    def webhook_path(self) -> str:
        return f"/webhook/{self.webhook_secret}"


settings = Settings()
