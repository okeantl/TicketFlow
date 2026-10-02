from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # postgresql
    DATABASE_URL: str

    # redis
    REDIS_URL: str

    # rabbitmq
    RABBITMQ_URL: str

    SECRET_KEY: str

    ENVIRONMENT: str

    LOG_LEVEL: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
