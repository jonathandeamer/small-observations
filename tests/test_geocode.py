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


def test_reverse_uses_county_when_no_city(tmp_path: Path):
    payload = {"address": {"country": "United Kingdom", "county": "Gwynedd"}}
    cache = tmp_path / "geocode.json"
    with patch("ingest.geocode.urlopen", _mock_urlopen(payload)):
        result = geocode.reverse(52.93, -4.08, cache_path=cache)
    assert result == ("United Kingdom", "Gwynedd")


def test_reverse_returns_country_only_when_no_settlement(tmp_path: Path):
    payload = {"address": {"country": "Antarctica"}}
    cache = tmp_path / "geocode.json"
    with patch("ingest.geocode.urlopen", _mock_urlopen(payload)):
        result = geocode.reverse(-80, 0, cache_path=cache)
    assert result == ("Antarctica", None)


def _mock_urlopen_by_zoom(payloads: dict[int, dict], seen: list[int]):
    """Like _mock_urlopen, but picks the payload by the request's zoom param."""
    from urllib.parse import parse_qs, urlparse

    class _Resp:
        def __init__(self, data: bytes):
            self._data = data
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return self._data

    def _open(req, timeout=None):
        zoom = int(parse_qs(urlparse(req.full_url).query)["zoom"][0])
        seen.append(zoom)
        return _Resp(json.dumps(payloads[zoom]).encode("utf-8"))
    return _open


# Real Nominatim shape for central Belfast: zoom 10 lands on a historic
# boundary with no settlement key; zoom 14 has city "Belfast City District".
BELFAST_ZOOM_10 = {"address": {"historic": "County Borough of Belfast", "country": "United Kingdom"}}
BELFAST_ZOOM_14 = {"address": {"suburb": "Carrick Hill", "city": "Belfast City District", "country": "United Kingdom"}}


def test_reverse_retries_at_higher_zoom_when_no_settlement(tmp_path: Path):
    seen: list[int] = []
    cache = tmp_path / "geocode.json"
    with patch("ingest.geocode.urlopen", _mock_urlopen_by_zoom({10: BELFAST_ZOOM_10, 14: BELFAST_ZOOM_14}, seen)), \
         patch("ingest.geocode._RATE_LIMIT_SECONDS", 0):
        result = geocode.reverse(54.6036, -5.9305, cache_path=cache)
    assert result == ("United Kingdom", "Belfast")
    assert seen == [10, 14]


def test_reverse_does_not_retry_when_city_found(tmp_path: Path):
    seen: list[int] = []
    cache = tmp_path / "geocode.json"
    with patch("ingest.geocode.urlopen", _mock_urlopen_by_zoom({10: NOMINATIM_RESPONSE_PARIS}, seen)):
        geocode.reverse(48.8566, 2.3522, cache_path=cache)
    assert seen == [10]


def test_reverse_returns_pair_of_nones_when_nothing(tmp_path: Path):
    payload = {"address": {}}
    cache = tmp_path / "geocode.json"
    with patch("ingest.geocode.urlopen", _mock_urlopen(payload)):
        result = geocode.reverse(0.0, 0.0, cache_path=cache)
    assert result == (None, None)
