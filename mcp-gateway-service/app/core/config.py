from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    auth_service_url: str = "http://localhost:8001"
    email_adapter_url: str = "http://localhost:8002"
    slack_adapter_url: str = "http://localhost:8003"
    whatsapp_adapter_url: str = "http://localhost:8004"
    redis_url: str = "redis://localhost:6379/0"
    mcp_sse_heartbeat_seconds: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
