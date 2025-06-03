# config/settings.py

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # MongoDB
    mongo_host: str = Field("localhost")
    mongo_port: int = Field(27017, env="MONGO_PORT")
    mongo_db: str = Field("kikihi", env="MONGO_DB")

    # Redis
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")

    # Celery
    celery_broker_url: str = Field("redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        "redis://localhost:6379/1", env="CELERY_RESULT_BACKEND"
    )

    # FastAPI
    app_env: str = Field("development", env="APP_ENV")
    app_port: int = Field(8001, env="APP_PORT")
    debug: bool = Field(True, env="DEBUG")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def mongo_uri(self) -> str:
        return f"mongodb://{self.mongo_host}:{self.mongo_port}/{self.mongo_db}"


# 사용
settings = Settings()  # type: ignore
