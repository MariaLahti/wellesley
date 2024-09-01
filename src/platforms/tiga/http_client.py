from __future__ import annotations

from typing import Any, Dict, Optional

from ..common.base_http_client import BaseHttpClient
from ..common.config import BaseConfig
from .config import TigaConfig


class TigaHttpClient(BaseHttpClient):
    def __init__(self, base_config: BaseConfig, tiga_config: TigaConfig) -> None:
        super().__init__(base_config, tiga_config)
        self._tiga_config = tiga_config

    def _get_default_headers(self) -> Dict[str, str]:
        headers = super()._get_default_headers()
        headers.update({
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
        })
        return headers

    def post(self, path: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return self.request("POST", path, data=data, headers=headers)


__all__ = ["TigaHttpClient"]