import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class AppConfig:
    base_url: str
    timeout_seconds: float
    retry_total: int
    retry_backoff: float
    # optional random delay (seconds)
    delay_min_seconds: float | None
    delay_max_seconds: float | None

    # web auth & session
    web_username: str | None
    web_password: str | None
    secret_key: str

    # api params
    city_id: str | None
    device: str | None
    device_uu_token: str | None
    channel: str | None
    platform: str | None
    sys_version: str | None
    user_agent: str | None
    accept_language: str | None
    registration_id: str | None
    token: str | None

    # db
    database_url: str

    # scheduler & categories
    schedule_interval_minutes: int
    domestic_category_id: str | None
    overseas_category_id: str | None
    max_pages: int | None


def load_config() -> AppConfig:
    load_dotenv(override=False)

    base_url = os.getenv("BASE_URL", "https://app.example.com")
    timeout_seconds = float(os.getenv("TIMEOUT_SECONDS", "15"))
    retry_total = int(os.getenv("RETRY_TOTAL", "3"))
    retry_backoff = float(os.getenv("RETRY_BACKOFF", "0.5"))

    return AppConfig(
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        retry_total=retry_total,
        retry_backoff=retry_backoff,
        delay_min_seconds=(float(os.getenv("DELAY_MIN_SECONDS")) if os.getenv("DELAY_MIN_SECONDS") else None),
        delay_max_seconds=(float(os.getenv("DELAY_MAX_SECONDS")) if os.getenv("DELAY_MAX_SECONDS") else None),
        web_username=os.getenv("WEB_USERNAME"),
        web_password=os.getenv("WEB_PASSWORD"),
        secret_key=os.getenv("SECRET_KEY", "please-change-me"),
        city_id=os.getenv("CITY_ID"),
        device=os.getenv("DEVICE"),
        device_uu_token=os.getenv("DEVICE_UU_TOKEN"),
        channel=os.getenv("CHANNEL"),
        platform=os.getenv("PLATFORM"),
        sys_version=os.getenv("SYS_VERSION"),
        user_agent=os.getenv("USER_AGENT"),
        accept_language=os.getenv("ACCEPT_LANGUAGE"),
        registration_id=os.getenv("REGISTRATION_ID"),
        token=os.getenv("TOKEN"),
        database_url=os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/wellesley"),
        schedule_interval_minutes=int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "30")),
        domestic_category_id=os.getenv("DOMESTIC_CATEGORY_ID"),
        overseas_category_id=os.getenv("OVERSEAS_CATEGORY_ID"),
        max_pages=(int(os.getenv("MAX_PAGES")) if os.getenv("MAX_PAGES") else None),
    )


__all__ = ["AppConfig", "load_config"]

