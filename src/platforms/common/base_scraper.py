from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from datetime import date

from ...db import Database


class BaseScraper(ABC):
    def __init__(self, db: Database) -> None:
        self._log = logging.getLogger(__name__)
        self._db = db

    @abstractmethod
    def get_platform_name(self) -> str:
        pass

    @abstractmethod
    def scrape_activities(self, max_pages: Optional[int] = None) -> None:
        pass

    def save_activity_data(self, activity_id: str, date_key: str, activity_data: Dict[str, Any], type_text: str) -> None:
        self._db.save_activity_detail(
            activity_id=str(activity_id),
            date_key=date_key,
            activity_data=activity_data,
            type_text=type_text,
            platform=self.get_platform_name(),
        )


__all__ = ["BaseScraper"]