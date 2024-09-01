from __future__ import annotations

from typing import Any, Dict, Optional

from ..common.base_http_client import BaseHttpClient
from ..common.config import BaseConfig
from .config import GaiaConfig


class GaiaHttpClient(BaseHttpClient):
    def __init__(self, base_config: BaseConfig, gaia_config: GaiaConfig) -> None:
        super().__init__(base_config, gaia_config)
        self._gaia_config = gaia_config

    def _get_default_headers(self) -> Dict[str, str]:
        headers = super()._get_default_headers()
        headers.update({
            "content-type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Platform": "USER_WECHAT_APPLET",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Avg-Attribute": "",
            "Share-Token": "",
            "User-Token": "",
            "Avg-Expires-Time": "",
            "First-Attribute": "",
        })
        return headers

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return self.request("GET", path, params=params, headers=headers)


__all__ = ["GaiaHttpClient"]
