from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from ..domain.calendar_entry import CalendarEntry


class TheSportsDBClient:
    def __init__(
        self,
        base_url: str,
        free_api_key: str,
        opener=urlopen,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.free_api_key = free_api_key
        self.opener = opener

    def fetch_json(self, entry: CalendarEntry, endpoint: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{self.base_url}/{self.api_key_for(entry)}/{endpoint}?{urlencode(params)}"
        with self.opener(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def api_key_for(self, entry: CalendarEntry) -> str:
        if not entry.api_key_provider:
            return self.free_api_key
        return os.environ.get(entry.api_key_provider, self.free_api_key)
