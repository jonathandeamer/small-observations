"""Reverse-geocode (lat, lon) to (country, city) using Nominatim, with on-disk cache.

Nominatim has a 1-request-per-second usage policy. We don't enforce it here
beyond setting a User-Agent — for a ≤200-photo batch with caching, calls are
rare enough that polling stays well under the limit.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USER_AGENT = "small-observations-ingest/0.1 (personal blog tool)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

# Preference order: Nominatim's address keys differ for tiny vs large places.
_CITY_KEYS = ("city", "town", "village", "hamlet", "suburb", "municipality")

# Nominatim's usage policy is max 1 request/second. We enforce a soft floor.
_RATE_LIMIT_SECONDS = 1.1
_last_request_at: float = 0.0


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


def _query_nominatim(lat: float, lon: float) -> Optional[dict]:
    """Return the Nominatim payload, or None on transient HTTP failure.

    Rate-limited to 1 request per ~1.1s. On 429 we back off and retry once.
    """
    global _last_request_at

    params = urlencode({"lat": lat, "lon": lon, "format": "json", "zoom": 10, "addressdetails": 1})
    req = Request(f"{NOMINATIM_URL}?{params}", headers={"User-Agent": USER_AGENT})

    for attempt in (1, 2):
        wait = _RATE_LIMIT_SECONDS - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
        try:
            with urlopen(req, timeout=15) as resp:
                _last_request_at = time.monotonic()
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            _last_request_at = time.monotonic()
            if e.code == 429 and attempt == 1:
                time.sleep(5)  # extra cool-down before retry
                continue
            print(f"  warn  nominatim http {e.code} for ({lat}, {lon})")
            return None
        except URLError as e:
            _last_request_at = time.monotonic()
            print(f"  warn  nominatim network error for ({lat}, {lon}): {e.reason}")
            return None
    return None


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
    if payload is None:
        return None
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
