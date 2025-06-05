from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).with_name("config.json")


@lru_cache(maxsize=1)
def _load_config() -> dict[str, Any]:
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get(key: str, default: Any = None) -> Any:
    """Return configuration value for ``key`` or ``default`` if missing."""
    return _load_config().get(key, default)
