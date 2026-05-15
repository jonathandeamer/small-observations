"""Reverse-geocode (lat, lon) to (country, city) using Nominatim, with on-disk cache.

Nominatim has a 1-request-per-second usage policy. We don't enforce it here
beyond setting a User-Agent — for a ≤200-photo batch with caching, calls are
rare enough that polling stays well under the limit.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USER_AGENT = "small-observations-ingest/0.1 (personal blog tool)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

# Preference order: Nominatim's address keys differ for tiny vs large places.
_CITY_KEYS = ("city", "town", "village", "hamlet", "suburb", "municipality")


def _cache_key(lat: float, lon: float) -> str:
    # Round to 4 decimals (~10m precision) so neighboring shots share a cache hit.
    return f"{round(lat, 4)},{round(lon, 4)}"


def _load_cache(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def _query_nominatim(lat: float, lon: float) -> dict:
    params = urlencode({"lat": lat, "lon": lon, "format": "json", "zoom": 10, "addressdetails": 1})
    req = Request(f"{NOMINATIM_URL}?{params}", headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def reverse(lat: float, lon: float, *, cache_path: Path) -> Optional[tuple[str, str]]:
    """Return (country, city) for the coordinates, or None if either is missing."""
    key = _cache_key(lat, lon)
    cache = _load_cache(cache_path)
    if key in cache:
        entry = cache[key]
        if entry.get("country") and entry.get("city"):
            return (entry["country"], entry["city"])
        return None

    payload = _query_nominatim(lat, lon)
    address = payload.get("address", {}) or {}

    country = address.get("country")
    city = None
    for k in _CITY_KEYS:
        if v := address.get(k):
            city = v
            break

    cache[key] = {"country": country, "city": city}
    _save_cache(cache_path, cache)

    if not country or not city:
        return None
    return (country, city)
