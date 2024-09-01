from __future__ import annotations

from typing import Any, Dict, Optional
import logging
from datetime import date

from .config import AppConfig
from .db import Database
from .http_client import HttpClient


class Scraper:
    def __init__(self, config: AppConfig, db: Database, http: HttpClient) -> None:
        self._log = logging.getLogger(__name__)
        self._config = config
        self._db = db
        self._http = http

    def scrape_domestic(self, category_id: str, page: int) -> Dict[str, Any]:
        self._log.info("scrape_domestic category_id=%s page=%s", category_id, page)
        data = {
            "id": str(category_id),
            "is_fanti": "0",
            "page": str(page),
            "platform": self._config.platform or "1",
            "registration_id": self._config.registration_id or "",
            "sys_version": self._config.sys_version or "",
            "token": self._config.token or "",
            "version": (self._config.user_agent.split("/")[1].split(" ")[0] if self._config.user_agent and "/" in self._config.user_agent else ""),
        }
        resp = self._http.post("/api/v2/list/datas", data)
        return resp

    def scrape_overseas(self, category_id: str, page: int) -> Dict[str, Any]:
        self._log.info("scrape_overseas category_id=%s page=%s", category_id, page)
        data = {
            "channel": self._config.channel or "appstore",
            "city_id": self._config.city_id or "",
            "device": self._config.device or "",
            "device_uu_token": self._config.device_uu_token or "",
            "id": str(category_id),
            "is_fanti": "0",
            "page": str(page),
            "platform": self._config.platform or "1",
            "registration_id": self._config.registration_id or "",
            "sys_version": self._config.sys_version or "",
            "token": self._config.token or "",
            "version": (self._config.user_agent.split("/")[1].split(" ")[0] if self._config.user_agent and "/" in self._config.user_agent else ""),
        }
        resp = self._http.post("/api/v2/list/datas", data)
        return resp

    def scrape_activity_detail(self, activity_id: str, type_value: int = 0, stat_param: Optional[str] = None, source_type: str = "") -> Dict[str, Any]:
        self._log.info("scrape_detail activity_id=%s type=%s", activity_id, type_value)
        data = {
            "channel": self._config.channel or "appstore",
            "city_id": self._config.city_id or "",
            "device": (self._config.device or "").replace(",", "%2C"),
            "device_uu_token": self._config.device_uu_token or "",
            "id": str(activity_id),
            "is_fanti": "0",
            "platform": self._config.platform or "1",
            "registration_id": self._config.registration_id or "",
            "sys_version": self._config.sys_version or "",
            "token": self._config.token or "",
            "type": str(type_value),
            "version": (self._config.user_agent.split("/")[1].split(" ")[0] if self._config.user_agent and "/" in self._config.user_agent else ""),
        }
        if stat_param:
            data["stat_param"] = stat_param
        resp = self._http.post("/api/v1/activity/detail", data)
        # 判断返回码，失败则仅日志不入库
        code = resp.get("code")
        if code != 200:
            self._log.error("detail_failed activity_id=%s code=%s", activity_id, code)
            return resp
        # 保存按天唯一，仅存data内容
        self._db.save_activity_detail(
            activity_id=str(activity_id),
            date_key=date.today().isoformat(),
            activity_data=(resp.get("data") or {}),
            type_text=source_type or "",
        )
        return resp

    def scrape_all_pages_and_details(self, domestic_category_id: str, overseas_category_id: str, max_pages: Optional[int] = None) -> None:
        self._log.info("job_start domestic_id=%s overseas_id=%s max_pages=%s", domestic_category_id, overseas_category_id, max_pages)
        # domestic pages
        page = 0
        while True:
            if max_pages and page > max_pages:
                break
            dom = self.scrape_domestic(domestic_category_id, page)
            items = (dom.get("data") or {}).get("items") or []
            # 列表接口失败也要输出日志
            if dom.get("code") != 200:
                self._log.error("domestic_failed page=%s code=%s", page, dom.get("code"))
                break
            self._log.info("domestic_page_result page=%s items=%s", page, len(items))
            # detail for each item using jump_id if present, else fallback to id
            for it in items:
                jump_id = it.get("jump_id") if it else None
                aid = str(jump_id if jump_id is not None else it.get("id") if it and it.get("id") is not None else None)
                if aid:
                    self.scrape_activity_detail(aid, type_value=0, source_type="domestic")
            total = (dom.get("data") or {}).get("total") or 0
            if not items or page * len(items) >= int(total):
                break
            page += 1

        # overseas pages
        page = 0
        while True:
            if max_pages and page > max_pages:
                break
            over = self.scrape_overseas(overseas_category_id, page)
            items = (over.get("data") or {}).get("items") or []
            if over.get("code") != 200:
                self._log.error("overseas_failed page=%s code=%s", page, over.get("code"))
                break
            self._log.info("overseas_page_result page=%s items=%s", page, len(items))
            for it in items:
                jump_id = it.get("jump_id") if it else None
                aid = str(jump_id if jump_id is not None else it.get("id") if it and it.get("id") is not None else None)
                if aid:
                    self.scrape_activity_detail(aid, type_value=0, source_type="overseas")
            total = (over.get("data") or {}).get("total") or 0
            if not items or page * len(items) >= int(total):
                break
            page += 1
        self._log.info("job_end")


__all__ = ["Scraper"]

