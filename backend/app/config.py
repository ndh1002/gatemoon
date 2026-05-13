from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://moonhunter:moonhunter@localhost:5432/moonhunter"
    redis_url: str = "redis://localhost:6379/0"

    gate_api_key: str = ""
    gate_api_secret: str = ""

    scan_interval_seconds: int = 12
    top_symbols_by_quote_volume: int = 80
    min_quote_volume_usdt: float = 500_000.0

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_min_moonshot_score: float = 72.0
    telegram_max_risk_score: float = 45.0
    telegram_cooldown_minutes: int = 30

    twitter_bearer_token: str = ""

    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
