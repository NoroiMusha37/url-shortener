from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    SIGNING_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RETRIES_NUM: int = 3
    SHORT_CODE_LENGTH: int = 8
    TOP_REFERRERS: int = 5

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        extra="ignore"
    )


settings = Settings()
