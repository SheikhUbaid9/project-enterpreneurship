from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/email_db"
    auth_service_url: str = "http://localhost:8001"
    token_encryption_key: str = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    mock_mode: bool = True
    mock_seed_message_count: int = 12

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("mock_seed_message_count")
    @classmethod
    def validate_seed_count(cls, value: int) -> int:
        if value < 1:
            raise ValueError("mock_seed_message_count must be >= 1")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
