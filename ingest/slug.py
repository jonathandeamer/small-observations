"""Build a stable slug for a photo post."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Iterable, Optional


def _slugify(text: str) -> str:
    """Lowercase, strip diacritics, replace non-alphanumeric with hyphens."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def build(date: datetime, *, city: Optional[str], existing: Iterable[str]) -> str:
    """Return a slug like `2018-07-14-paris`, unique within `existing`."""
    parts = [date.strftime("%Y-%m-%d")]
    if city:
        city_slug = _slugify(city)
        if city_slug:
            parts.append(city_slug)
    base = "-".join(parts)

    existing_set = set(existing)
    if base not in existing_set:
        return base

    n = 2
    while f"{base}-{n}" in existing_set:
        n += 1
    return f"{base}-{n}"
