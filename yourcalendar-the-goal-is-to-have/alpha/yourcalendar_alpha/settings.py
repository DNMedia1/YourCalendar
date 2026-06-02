from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_settings(path: str | Path | None = None) -> dict[str, Any]:
    settings_path = Path(path) if path else ROOT_DIR / "settings.json"
    if not settings_path.is_absolute():
        settings_path = ROOT_DIR / settings_path
    with settings_path.open("r", encoding="utf-8") as handle:
        settings = json.load(handle)
    settings["_root_dir"] = str(ROOT_DIR)
    return settings


def resolve_path(settings: dict[str, Any], value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return Path(settings["_root_dir"]) / path
