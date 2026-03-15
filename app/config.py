import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LMS_API_KEY: str
    LOG_LEVEL: str = "INFO"

    POSTGRES_DATABASE_NAME: str
    POSTGRES_HOST: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int
    POSTGRES_USER: Optional[str] = None

    POSTGRES_CONNECTION_STRING: Optional[str] = None

    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 0.5

    CAPASHINO_BASE_URL: str = "https://capashino.dev-2.python-labs.ru"
    BATCH_SIZE_OUTBOX_TASKS: int = 10
    POLL_INTERVAL_OUTBOX: int = 5
    MAX_RETRIES_OUTBOX: int = 5
    DAYS_TO_KEEP: int = 7
    TTL_DAYS_IDM_KEYS: int = 7

    K8S_SERVICE_NAME: str
    K8S_NAMESPACE: str
    K8S_SERVICE_PORT: str

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self, **data):
        super().__init__(**data)
        if self.POSTGRES_CONNECTION_STRING:
            if self.POSTGRES_CONNECTION_STRING.startswith("postgres://"):
                self.POSTGRES_CONNECTION_STRING = (
                    self.POSTGRES_CONNECTION_STRING.replace(
                        "postgres://", "postgresql+asyncpg://", 1
                    )
                )
        else:
            self.POSTGRES_CONNECTION_STRING = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE_NAME}"
            )

    @property
    def callback_url(self):
        return (
            f"http://"
            f"{settings.K8S_SERVICE_NAME}."
            f"{settings.K8S_NAMESPACE}.svc.cluster.local:"
            f"{settings.K8S_SERVICE_PORT}"
        )


if os.getenv("DOCKER_ENV") == "true":
    settings = Settings()
else:
    env_file = os.path.join(Path(__file__).parent.parent, ".env")
    settings = Settings(_env_file=env_file)

print(settings.POSTGRES_CONNECTION_STRING)
