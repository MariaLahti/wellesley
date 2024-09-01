from __future__ import annotations

import time
from typing import Any, Dict, Optional
import logging
import random

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import BaseConfig, PlatformConfig


class BaseHttpClient:
    def __init__(self, base_config: BaseConfig, platform_config: PlatformConfig) -> None:
        self._log = logging.getLogger(__name__)
        self._base_config = base_config
        self._platform_config = platform_config
        self._session = requests.Session()

        retry = Retry(
            total=base_config.retry_total,
            backoff_factor=base_config.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def _apply_delay(self) -> None:
        if self._base_config.delay_min_seconds is not None and self._base_config.delay_max_seconds is not None:
            delay = random.uniform(self._base_config.delay_min_seconds, self._base_config.delay_max_seconds)
            if delay > 0:
                self._log.info("http_delay seconds=%s", round(delay, 3))
                time.sleep(delay)

    def _get_base_url(self) -> str:
        return self._platform_config.base_url.rstrip("/")

    def _get_default_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Connection": "keep-alive",
        }
        if self._platform_config.user_agent:
            headers["User-Agent"] = self._platform_config.user_agent
        if self._platform_config.accept_language:
            headers["Accept-Language"] = self._platform_config.accept_language
        return headers

    def request(self, method: str, path: str, data: Optional[Dict[str, Any]] = None, 
                params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = self._get_base_url() + path
        merged_headers = self._get_default_headers()
        if headers:
            merged_headers.update(headers)

        self._log.info("http_request method=%s url=%s", method, url)
        self._apply_delay()

        if method.upper() == "POST":
            response = self._session.post(url, data=data, headers=merged_headers, timeout=self._base_config.timeout_seconds)
        elif method.upper() == "GET":
            response = self._session.get(url, params=params, headers=merged_headers, timeout=self._base_config.timeout_seconds)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        self._log.info("http_response status=%s url=%s", response.status_code, url)
        response.raise_for_status()
        return response.json()


__all__ = ["BaseHttpClient"]