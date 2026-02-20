from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/auth_db"
    jwt_secret_key: str = "change-this-super-secret-key-for-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120

    seed_owner_email: str = "owner@inbox.local"
    seed_owner_password: str = "OwnerPass!123"
    seed_admin_email: str = "admin@inbox.local"
    seed_admin_password: str = "AdminPass!123"
    seed_member_email: str = "member@inbox.local"
    seed_member_password: str = "MemberPass!123"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
