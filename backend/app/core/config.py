from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SGE Aquachile"
    api_v1_prefix: str = ""
    environment: str = "development"
    database_url: str = Field(default="sqlite:///./sge_aquachile.db", alias="DATABASE_URL")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    cors_origins: str = Field(default="http://localhost:3000,http://127.0.0.1:3000", alias="CORS_ORIGINS")
    seed_admin_username: str = "admin"
    seed_admin_password: str = "Admin1234!"
    seed_admin_email: str = "admin@sge-aquachile.local"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

