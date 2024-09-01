import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class BaseConfig:
    database_url: str
    timeout_seconds: float
    retry_total: int
    retry_backoff: float
    delay_min_seconds: Optional[float]
    delay_max_seconds: Optional[float]
    web_username: Optional[str]
    web_password: Optional[str]
    secret_key: str
    tiga_display_name: str
    gaia_display_name: str

    @classmethod
    def from_env(cls) -> "BaseConfig":
        load_dotenv(override=False)
        return cls(
            database_url=os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/wellesley"),
            timeout_seconds=float(os.getenv("TIMEOUT_SECONDS", "15")),
            retry_total=int(os.getenv("RETRY_TOTAL", "3")),
            retry_backoff=float(os.getenv("RETRY_BACKOFF", "0.5")),
            delay_min_seconds=(float(os.getenv("DELAY_MIN_SECONDS")) if os.getenv("DELAY_MIN_SECONDS") else None),
            delay_max_seconds=(float(os.getenv("DELAY_MAX_SECONDS")) if os.getenv("DELAY_MAX_SECONDS") else None),
            web_username=os.getenv("WEB_USERNAME"),
            web_password=os.getenv("WEB_PASSWORD"),
            secret_key=os.getenv("SECRET_KEY", "please-change-me"),
            tiga_display_name=os.getenv("TIGA_DISPLAY_NAME", "Tiga"),
            gaia_display_name=os.getenv("GAIA_DISPLAY_NAME", "Gaia"),
        )


@dataclass  
class PlatformConfig:
    base_url: str
    user_agent: Optional[str]
    accept_language: Optional[str]
    
    def __init__(self, prefix: str):
        load_dotenv(override=False)
        self.base_url = os.getenv(f"{prefix}_BASE_URL", "")
        self.user_agent = os.getenv(f"{prefix}_USER_AGENT")
        self.accept_language = os.getenv(f"{prefix}_ACCEPT_LANGUAGE")


__all__ = ["BaseConfig", "PlatformConfig"]