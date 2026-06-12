from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # REQUIRED — no default intentionally; app fails fast if DATABASE_URL is missing
    DATABASE_URL: str

    JWT_SECRET: str = "changeme_dev_only_not_for_production"
    JWT_EXPIRE_MIN: int = 60

    FCM_FAKE: bool = False
    FIREBASE_PROJECT_ID: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()
