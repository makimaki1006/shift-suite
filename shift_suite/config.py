from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any
import os

from .logger_config import configure_logging


configure_logging()
log = logging.getLogger(__name__)

_CONFIG_PATH = Path(
    os.getenv("SHIFT_SUITE_CONFIG", str(Path(__file__).with_name("config.json")))
)


@lru_cache(maxsize=1)
def _load_config() -> dict[str, Any]:
    if not _CONFIG_PATH.exists():
        log.warning("Configuration file %s not found", _CONFIG_PATH)
        return {}
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log.error("Failed to parse JSON configuration %s: %s", _CONFIG_PATH, e)
        return {}
    except Exception as e:  # pragma: no cover - fallback for unexpected errors
        log.error("Failed to load configuration %s: %s", _CONFIG_PATH, e)
        return {}


def get(key: str, default: Any = None) -> Any:
    """Return configuration value for ``key`` or ``default`` if missing."""
    return _load_config().get(key, default)


def reload_config() -> None:
    """Clear cached configuration so it will be reloaded on next access."""
    _load_config.cache_clear()


__all__ = ["get", "reload_config"]
