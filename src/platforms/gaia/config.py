import os
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv

from ..common.config import PlatformConfig


@dataclass
class GaiaConfig(PlatformConfig):
    schedule_interval_minutes: int
    max_pages: Optional[int]
    catalogs: List[str]

    def __init__(self):
        super().__init__("GAIA")
        load_dotenv(override=False)
        
        self.schedule_interval_minutes = int(os.getenv("GAIA_SCHEDULE_INTERVAL_MINUTES", "60"))
        self.max_pages = (int(os.getenv("GAIA_MAX_PAGES")) if os.getenv("GAIA_MAX_PAGES") else None)
        catalogs_str = os.getenv("GAIA_CATALOGS", "E,L,SW,S,WE,SY")
        self.catalogs = [c.strip() for c in catalogs_str.split(",") if c.strip()]


__all__ = ["GaiaConfig"]