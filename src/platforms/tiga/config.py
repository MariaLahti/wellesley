import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

from ..common.config import PlatformConfig


@dataclass
class TigaConfig(PlatformConfig):
    city_id: Optional[str]
    device: Optional[str]
    device_uu_token: Optional[str]
    channel: Optional[str]
    platform: Optional[str]
    sys_version: Optional[str]
    registration_id: Optional[str]
    token: Optional[str]
    schedule_interval_minutes: int
    domestic_category_id: Optional[str]
    overseas_category_id: Optional[str]
    max_pages: Optional[int]

    def __init__(self):
        super().__init__("TIGA")
        load_dotenv(override=False)
        
        self.city_id = os.getenv("TIGA_CITY_ID")
        self.device = os.getenv("TIGA_DEVICE")
        self.device_uu_token = os.getenv("TIGA_DEVICE_UU_TOKEN")
        self.channel = os.getenv("TIGA_CHANNEL")
        self.platform = os.getenv("TIGA_PLATFORM")
        self.sys_version = os.getenv("TIGA_SYS_VERSION")
        self.registration_id = os.getenv("TIGA_REGISTRATION_ID")
        self.token = os.getenv("TIGA_TOKEN")
        self.schedule_interval_minutes = int(os.getenv("TIGA_SCHEDULE_INTERVAL_MINUTES", "30"))
        self.domestic_category_id = os.getenv("TIGA_DOMESTIC_CATEGORY_ID")
        self.overseas_category_id = os.getenv("TIGA_OVERSEAS_CATEGORY_ID")
        self.max_pages = (int(os.getenv("TIGA_MAX_PAGES")) if os.getenv("TIGA_MAX_PAGES") else None)


__all__ = ["TigaConfig"]