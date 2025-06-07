# config/settings.py
import os
from functools import lru_cache

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_env: str = Field("development", env="APP_ENV")

    # MongoDB
    mongo_host: str = Field(..., env="MONGO_HOST")
    mongo_port: int = Field(27017, env="MONGO_PORT")
    mongo_db: str = Field(..., env="MONGO_DB")

    # Redis
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")

    # Celery
    celery_broker_url: str = Field("redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field("redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")

    class Config:
        env_file = ".env.production"  # 기본값은 .env, 커스터마이징은 아래에서 수행
        env_file_encoding = "utf-8"

    @property
    def mongo_uri(self) -> str:
        return f"mongodb://{self.mongo_host}:{self.mongo_port}/{self.mongo_db}"


@lru_cache()
def get_settings() -> Settings:
    env = os.getenv("APP_ENV", "development")
    env_path = f".env.{env}"
    return Settings(_env_file=env_path)  # type: ignore


# 사용 예시
settings = get_settings()
