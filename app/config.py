from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "change-this-to-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 14  # 14 days

    DATABASE_URL: str = "sqlite:///./partner_app.db"

    GOOGLE_CLIENT_ID: str = ""  # from Google Cloud Console, used to verify id_tokens

    HP_MAX: int = 10
    HP_DEFAULT_DECAY_HOURS: int = 6  # hp drops by 1 every N hours of silence

    MEDIA_DIR: str = "media"  # local dev storage for images/voice/video (NOT for private/vault media)

    class Config:
        env_file = ".env"


settings = Settings()
