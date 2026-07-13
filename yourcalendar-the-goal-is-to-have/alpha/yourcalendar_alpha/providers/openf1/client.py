from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


class OpenF1Client:
    def __init__(
        self,
        base_url: str,
        opener=urlopen,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.opener = opener

    def fetch_json(self, endpoint: str, params: dict[str, str]) -> list[dict[str, Any]]:
        query = urlencode(params)
        url = f"{self.base_url}/{endpoint}"
        if query:
            url = f"{url}?{query}"
        with self.opener(url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, list):
            return []
        return [item for item in payload if isinstance(item, dict)]
