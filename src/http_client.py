from __future__ import annotations

import time
from typing import Any, Dict, Optional
import logging
import random
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import AppConfig


class HttpClient:
    def __init__(self, config: AppConfig) -> None:
        self._log = logging.getLogger(__name__)
        self._config = config
        self._session = requests.Session()

        retry = Retry(
            total=config.retry_total,
            backoff_factor=config.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def _default_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Connection": "keep-alive",
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        if self._config.user_agent:
            headers["User-Agent"] = self._config.user_agent
        if self._config.accept_language:
            headers["Accept-Language"] = self._config.accept_language
        return headers

    def post(self, path: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = self._config.base_url.rstrip("/") + path
        merged_headers = self._default_headers()
        if headers:
            merged_headers.update(headers)

        self._log.info("http_request method=POST url=%s", url)
        # random delay to reduce server pressure
        if self._config.delay_min_seconds is not None and self._config.delay_max_seconds is not None:
            delay = random.uniform(self._config.delay_min_seconds, self._config.delay_max_seconds)
            if delay > 0:
                self._log.info("http_delay seconds=%s", round(delay, 3))
                time.sleep(delay)
        response = self._session.post(url, data=data, headers=merged_headers, timeout=self._config.timeout_seconds)
        self._log.info("http_response status=%s url=%s", response.status_code, url)
        response.raise_for_status()
        return response.json()


__all__ = ["HttpClient"]

