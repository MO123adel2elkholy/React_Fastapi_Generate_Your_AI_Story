import json
from typing import List
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./database.db"
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_HOST: str | None = None
    DB_PORT: str | int | None = None
    DB_NAME: str | None = None

    ALLOWED_ORIGINS: List[str] = []
    OPENAI_API_KEY: str

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v) -> List[str]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(origin).strip() for origin in parsed if str(origin).strip()]
            except json.JSONDecodeError:
                pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v or []

    @model_validator(mode="after")
    def build_database_url(self):
        if self.DATABASE_URL and self.DATABASE_URL != "sqlite:///./database.db":
            return self

        if self.DEBUG:
            self.DATABASE_URL = "sqlite:///./database.db"
            return self

        required = [self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_PORT, self.DB_NAME]
        if all(required):
            self.DATABASE_URL = (
                f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
            return self

        raise ValueError(
            "Production database not configured. Set DATABASE_URL or "
            "DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME."
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()