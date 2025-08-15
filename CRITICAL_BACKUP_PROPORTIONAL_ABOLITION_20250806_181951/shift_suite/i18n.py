from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

_LOCALE_DIR = Path(__file__).with_name("resources")
_DEFAULT_LANG = "ja"


@lru_cache(maxsize=4)
def load_translations(lang: str = _DEFAULT_LANG) -> Dict[str, str]:
    fp = _LOCALE_DIR / f"strings_{lang}.json"
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def translate(text: str, lang: str = _DEFAULT_LANG) -> str:
    """Return the translated text for ``lang`` or the key itself."""
    return load_translations(lang).get(text, text)
