from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging
from datetime import date

from ...db import Database
from ..common.base_scraper import BaseScraper
from .http_client import GaiaHttpClient
from .config import GaiaConfig


class GaiaScraper(BaseScraper):
    def __init__(self, db: Database, http_client: GaiaHttpClient, config: GaiaConfig) -> None:
        super().__init__(db)
        self._log = logging.getLogger(__name__)
        self._http = http_client
        self._config = config

    def get_platform_name(self) -> str:
        return "gaia"

    def scrape_list(self, catalog: str, page_index: int = 1, page_size: int = 20) -> Dict[str, Any]:
        self._log.info("scrape_gaia_list catalog=%s page_index=%s", catalog, page_index)
        path = f"/sku-wide?catalog={catalog}&packet=forSale&pageScene=page&pageIndex={page_index}&pageSize={page_size}"
        resp = self._http.get(path)
        return resp

    def scrape_detail(self, sku_original_id: str) -> Dict[str, Any]:
        self._log.info("scrape_gaia_detail sku_id=%s", sku_original_id)
        path = f"/sku/detail?skuOriginalId={sku_original_id}"
        resp = self._http.get(path)
        return resp

    def scrape_times(self, sku_original_id: str) -> Dict[str, Any]:
        self._log.info("scrape_gaia_times sku_id=%s", sku_original_id)
        path = f"/trip-wide?pageScene=dayGroup&skuWideId=0&skuOriginalId={sku_original_id}"
        resp = self._http.get(path)
        return resp

    def scrape_activity_full(self, sku_original_id: str, activity_type: str) -> bool:
        detail_resp = self.scrape_detail(sku_original_id)
        if detail_resp.get("code") != 0:
            self._log.error("gaia_detail_failed sku_id=%s code=%s", sku_original_id, detail_resp.get("code"))
            return False
        
        times_resp = self.scrape_times(sku_original_id)
        if times_resp.get("code") != 0:
            self._log.error("gaia_times_failed sku_id=%s code=%s", sku_original_id, times_resp.get("code"))
            return False

        combined_data = {
            "detail": detail_resp.get("data", {}),
            "times": times_resp.get("data", {})
        }

        self.save_activity_data(
            activity_id=str(sku_original_id),
            date_key=date.today().isoformat(),
            activity_data=combined_data,
            type_text=activity_type,
        )
        return True

    def scrape_activities(self, max_pages: Optional[int] = None) -> None:
        catalogs = self._config.catalogs or ["E", "L", "SW", "S", "WE", "SY"]
        
        self._log.info("gaia_job_start catalogs=%s max_pages=%s", catalogs, max_pages)
        
        for catalog in catalogs:
            page_index = 1
            while True:
                if max_pages and page_index > max_pages:
                    break
                    
                list_resp = self.scrape_list(catalog, page_index)
                if list_resp.get("code") != 0:
                    self._log.error("gaia_list_failed catalog=%s page=%s code=%s", catalog, page_index, list_resp.get("code"))
                    break
                
                data = list_resp.get("data", {})
                items = data.get("page", [])
                pagination = data.get("pagination", {})
                total_page = pagination.get("totalPage", 0)
                
                self._log.info("gaia_list_result catalog=%s page=%s items=%s total_pages=%s", 
                              catalog, page_index, len(items), total_page)
                
                for item in items:
                    original_id = item.get("originalId")
                    if original_id:
                        self.scrape_activity_full(original_id, catalog)
                
                if page_index >= total_page or not items:
                    break
                    
                page_index += 1
        
        self._log.info("gaia_job_end")


__all__ = ["GaiaScraper"]