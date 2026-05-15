"""Tests for the reverse geocoder.

We mock urlopen so tests don't hit Nominatim. The on-disk cache is exercised
by the cache_roundtrip test.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from ingest import geocode


NOMINATIM_RESPONSE_PARIS = {
    "address": {
        "country": "France",
        "city": "Paris",
        "country_code": "fr",
    }
}


def _mock_urlopen(payload: dict):
    """Build a replacement for urlopen returning `payload`."""
    class _Resp:
        def __init__(self, data: bytes):
            self._data = data
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return self._data
    return lambda req, timeout=None: _Resp(json.dumps(payload).encode("utf-8"))


def test_reverse_returns_country_and_city(tmp_path: Path):
    cache = tmp_path / "geocode.json"
    with patch("ingest.geocode.urlopen", _mock_urlopen(NOMINATIM_RESPONSE_PARIS)):
        result = geocode.reverse(48.8566, 2.3522, cache_path=cache)
    assert result == ("France", "Paris")


def test_reverse_caches_result(tmp_path: Path):
    cache = tmp_path / "geocode.json"
    with patch("ingest.geocode.urlopen", _mock_urlopen(NOMINATIM_RESPONSE_PARIS)):
        geocode.reverse(48.8566, 2.3522, cache_path=cache)
        geocode.reverse(48.8566, 2.3522, cache_path=cache)
    assert json.loads(cache.read_text())["48.8566,2.3522"] == {"country": "France", "city": "Paris"}


def test_reverse_falls_back_when_city_missing(tmp_path: Path):
    payload = {"address": {"country": "Iceland", "town": "Vík í Mýrdal"}}
    cache = tmp_path / "geocode.json"
    with patch("ingest.geocode.urlopen", _mock_urlopen(payload)):
        result = geocode.reverse(63.4, -19.0, cache_path=cache)
    assert result == ("Iceland", "Vík í Mýrdal")


def test_reverse_returns_none_when_country_missing(tmp_path: Path):
    payload = {"address": {}}
    cache = tmp_path / "geocode.json"
    with patch("ingest.geocode.urlopen", _mock_urlopen(payload)):
        result = geocode.reverse(0.0, 0.0, cache_path=cache)
    assert result is None
