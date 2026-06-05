from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    #PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_DB: str = "taskflow"
    POSTGRES_DB_USER: str
    POSTGRES_DB_PASSWORD: str

    #JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    #App
    APP_NAME: str = "TaskFlow"
    DEBUG: bool = False

    #Path for uploaded files
    UPLOAD_DIR: str = "./uploads"

    #DB URL
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_DB_USER}:{self.POSTGRES_DB_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,  # важно для Docker
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()