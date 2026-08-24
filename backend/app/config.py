from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_app_title: str = "application"
    llm_model: str = "google/gemini-3.7-flash"
    llm_temperature: float = 0.2
    llm_timeout_seconds: float = 30.0

    retrieval_top_k: int = 3
    transcript_window: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()
