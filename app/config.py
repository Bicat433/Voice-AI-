"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./patients.db"
    port: int = 8000
    vapi_api_key: str = ""
    vapi_phone_number_id: str = ""
    openai_api_key: str = ""


settings = Settings()
