# Small Observations — Ingest Script Implementation Plan (Plan B)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A one-shot Python tool that takes original smartphone photos from `_ingest/`, extracts EXIF (date + GPS), reverse-geocodes location to country/city, resizes to a web-sized JPEG, and emits a Hugo markdown post with prefilled front matter.

**Architecture:** A small Python package `ingest/` with concerns split by file: EXIF reading, reverse geocoding (with on-disk cache), slug generation, front-matter rendering, image resizing, and orchestration. CLI entry via `python -m ingest`. Tests use real fixture JPEGs and mock the Nominatim HTTP call.

**Tech Stack:** Python ≥3.10. Runtime: Pillow only. Dev/test: pytest + piexif (for generating EXIF in test fixtures). HTTP via stdlib `urllib`. Front matter rendered by hand-written templating for stable field ordering.

**Output contract** (must match Plan A's content model exactly):

```yaml
---
title: ""
slug: "wynwood-mural"
date: 2019-11-22T14:05:00-05:00
publishDate: 2026-05-15T10:00:00Z
photo: 2019/11/wynwood-mural.jpg
countries: [United States]
cities: [Miami]
artists: []
tags: []
years: [2019]
weight: 0
exif:
  camera: "iPhone 11"
  lat: 25.8010
  lon: -80.1990
---
```

A `slug` field is always emitted (avoids URL collisions for title-less posts — learned in Plan A). Post URLs come from Hugo's permalink config `/<year>/<month>/<slug>/`.

**Commit convention:** `type(scope): subject`. Types: `content | feat | fix | style | refactor | docs | chore | build`. Scopes: `home | post | list | partial | css | font | taxonomy | ingest | photo | note | config | spec | mockup | deploy`. All ingest work uses scope `ingest` (or `config` for tooling). Lowercase start, no trailing period, ≤72 chars.

---

## File structure (final state)

```
pyproject.toml                    # Python project definition + deps
.python-version                   # pyenv hint, "3.11" or similar
.gitignore                        # add .venv/ and .cache/
ingest/
  __init__.py                     # empty
  __main__.py                     # CLI entry: scan _ingest/, process each
  exif.py                         # extract(path) -> ExifData | None
  geocode.py                      # reverse(lat, lon) -> (country, city) | None
  slug.py                         # build(date, city, existing) -> str
  frontmatter.py                  # render(metadata) -> str (full markdown)
  resize.py                       # to_web(src, dst, max_dim, quality)
  pipeline.py                     # process(path, content_root, asset_root) -> Result
tests/
  conftest.py                     # fixtures: tmp_path-based paths, sample JPEGs
  fixtures/
    with_gps.jpg                  # 100×100 JPEG with EXIF DateTime + GPS
    no_gps.jpg                    # 100×100 JPEG with EXIF DateTime only
    no_exif.jpg                   # 100×100 JPEG with no EXIF
  test_exif.py
  test_geocode.py
  test_slug.py
  test_frontmatter.py
  test_resize.py
  test_pipeline.py
.cache/                           # geocode cache (gitignored)
  geocode.json                    # {"lat,lon": {"country": "...", "city": "..."}}
```

Each Python module is small (≤80 lines) with one responsibility. Tests mirror the modules.

---

## Task 1: Project skeleton — pyproject.toml, .gitignore, package layout

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `ingest/__init__.py`
- Create: `tests/__init__.py`
- Modify: `.gitignore`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "small-observations-ingest"
version = "0.1.0"
description = "One-shot ingest pipeline for Small Observations photos."
requires-python = ">=3.10"
dependencies = [
  "Pillow>=10.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "piexif>=1.1",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-q"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["ingest*"]
exclude = ["tests*"]
```

- [ ] **Step 2: Create `.python-version`**

```
3.11
```

- [ ] **Step 3: Append to `.gitignore`**

Open `.gitignore`. After the existing contents, append:

```
# Python
.venv/
__pycache__/
*.pyc
.pytest_cache/

# Geocode cache (rebuildable)
.cache/
```

- [ ] **Step 4: Create empty package modules**

```bash
mkdir -p ingest tests/fixtures
touch ingest/__init__.py tests/__init__.py
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .python-version .gitignore ingest/__init__.py tests/__init__.py
git commit -m "chore(config): add python project scaffolding for ingest"
```

---

## Task 2: Set up venv, install, verify pytest runs

**Files:** none modified; this task creates the local environment only.

- [ ] **Step 1: Create the venv**

```bash
python3 -m venv .venv
source .venv/bin/activate
python --version    # confirm 3.10+
```

- [ ] **Step 2: Install the project in editable mode with dev deps**

```bash
pip install -e ".[dev]"
```

Expected: installs Pillow, pytest, piexif and the local `ingest` package. Should complete in <30 seconds.

- [ ] **Step 3: Verify pytest can discover an (empty) test suite**

```bash
pytest --collect-only
```

Expected: `no tests collected` (we haven't written any yet) — but pytest itself runs without error and exits cleanly.

- [ ] **Step 4: No commit (the venv is gitignored)**

The venv contents are not committed. From here on, **every Python command assumes the venv is active**. If you start a new shell, run `source .venv/bin/activate` first.

---

## Task 3: EXIF extraction (TDD)

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/fixtures/with_gps.jpg`, `tests/fixtures/no_gps.jpg`, `tests/fixtures/no_exif.jpg` (generated)
- Create: `tests/test_exif.py`
- Create: `ingest/exif.py`

- [ ] **Step 1: Create `tests/conftest.py` to generate fixture JPEGs at session start**

```python
"""Generate small JPEG fixtures with controlled EXIF metadata.

Fixtures are regenerated on every test session — keeps them in the repo
unnecessary and avoids drift between metadata and image content.
"""

from __future__ import annotations

import io
from pathlib import Path

import piexif
import pytest
from PIL import Image

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _solid_jpeg(color: tuple[int, int, int]) -> bytes:
    """Return a 100x100 solid-color JPEG as bytes."""
    img = Image.new("RGB", (100, 100), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


def _gps_ifd(lat: float, lon: float) -> dict:
    """Convert decimal lat/lon into the EXIF GPS IFD structure piexif expects."""
    def to_dms(value: float) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
        value = abs(value)
        deg = int(value)
        minutes_full = (value - deg) * 60
        minutes = int(minutes_full)
        seconds = round((minutes_full - minutes) * 60 * 10000)
        return ((deg, 1), (minutes, 1), (seconds, 10000))

    return {
        piexif.GPSIFD.GPSLatitudeRef: b"N" if lat >= 0 else b"S",
        piexif.GPSIFD.GPSLatitude: to_dms(lat),
        piexif.GPSIFD.GPSLongitudeRef: b"E" if lon >= 0 else b"W",
        piexif.GPSIFD.GPSLongitude: to_dms(lon),
    }


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures():
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    # with_gps.jpg — Paris, July 14 2018
    exif = {
        "0th":   {piexif.ImageIFD.Make: b"Apple", piexif.ImageIFD.Model: b"iPhone 7"},
        "Exif":  {piexif.ExifIFD.DateTimeOriginal: b"2018:07:14 16:23:00"},
        "GPS":   _gps_ifd(48.8566, 2.3522),
        "1st":   {},
        "thumbnail": None,
    }
    img_bytes = _solid_jpeg((200, 100, 80))
    piexif.insert(piexif.dump(exif), img_bytes, str(FIXTURE_DIR / "with_gps.jpg"))

    # no_gps.jpg — date but no GPS
    exif_no_gps = {
        "0th":   {piexif.ImageIFD.Make: b"Apple", piexif.ImageIFD.Model: b"iPhone 11"},
        "Exif":  {piexif.ExifIFD.DateTimeOriginal: b"2019:11:22 14:05:00"},
        "GPS":   {},
        "1st":   {},
        "thumbnail": None,
    }
    img_bytes = _solid_jpeg((80, 120, 100))
    piexif.insert(piexif.dump(exif_no_gps), img_bytes, str(FIXTURE_DIR / "no_gps.jpg"))

    # no_exif.jpg — nothing useful
    (FIXTURE_DIR / "no_exif.jpg").write_bytes(_solid_jpeg((150, 150, 150)))


@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURE_DIR
```

- [ ] **Step 2: Write the failing test for `ingest.exif.extract`**

Create `tests/test_exif.py`:

```python
from datetime import datetime
from pathlib import Path

import pytest

from ingest import exif


def test_extract_returns_date_and_gps_and_camera(fixture_dir: Path):
    data = exif.extract(fixture_dir / "with_gps.jpg")
    assert data is not None
    assert data.date == datetime(2018, 7, 14, 16, 23, 0)
    assert data.lat == pytest.approx(48.8566, abs=1e-3)
    assert data.lon == pytest.approx(2.3522, abs=1e-3)
    assert data.camera == "iPhone 7"


def test_extract_returns_partial_when_gps_missing(fixture_dir: Path):
    data = exif.extract(fixture_dir / "no_gps.jpg")
    assert data is not None
    assert data.date == datetime(2019, 11, 22, 14, 5, 0)
    assert data.lat is None
    assert data.lon is None
    assert data.camera == "iPhone 11"


def test_extract_returns_none_when_no_exif(fixture_dir: Path):
    data = exif.extract(fixture_dir / "no_exif.jpg")
    assert data is None or data.date is None
```

- [ ] **Step 3: Run the failing test**

```bash
pytest tests/test_exif.py -v
```

Expected: import error — `ingest.exif` doesn't exist yet.

- [ ] **Step 4: Implement `ingest/exif.py`**

```python
"""Extract EXIF metadata from a JPEG: date, GPS, camera model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ExifTags

_DATE_FMT = "%Y:%m:%d %H:%M:%S"


@dataclass(frozen=True)
class ExifData:
    date: Optional[datetime]
    lat: Optional[float]
    lon: Optional[float]
    camera: Optional[str]

    @property
    def is_usable(self) -> bool:
        """A photo is processable when it has date AND GPS."""
        return self.date is not None and self.lat is not None and self.lon is not None


def _dms_to_decimal(dms: tuple, ref: str) -> float:
    deg, minutes, seconds = dms
    value = float(deg) + float(minutes) / 60.0 + float(seconds) / 3600.0
    if ref in ("S", "W"):
        value = -value
    return value


def extract(path: Path) -> Optional[ExifData]:
    """Return an ExifData for `path`, or None if the file has no EXIF at all."""
    with Image.open(path) as img:
        raw = img.getexif()
        if not raw:
            return None

        # Resolve tag IDs to names so we can read by name.
        tags = {ExifTags.TAGS.get(t, t): v for t, v in raw.items()}

        date = None
        if raw_date := raw.get_ifd(ExifTags.IFD.Exif).get(ExifTags.Base.DateTimeOriginal):
            try:
                date = datetime.strptime(raw_date, _DATE_FMT)
            except (ValueError, TypeError):
                date = None

        camera = tags.get("Model")
        if isinstance(camera, bytes):
            camera = camera.decode("ascii", errors="replace").strip("\x00").strip()

        lat = lon = None
        gps = raw.get_ifd(ExifTags.IFD.GPSInfo)
        if gps:
            gps_named = {ExifTags.GPSTAGS.get(t, t): v for t, v in gps.items()}
            if all(k in gps_named for k in ("GPSLatitude", "GPSLatitudeRef",
                                            "GPSLongitude", "GPSLongitudeRef")):
                lat = _dms_to_decimal(gps_named["GPSLatitude"], gps_named["GPSLatitudeRef"])
                lon = _dms_to_decimal(gps_named["GPSLongitude"], gps_named["GPSLongitudeRef"])

    return ExifData(date=date, lat=lat, lon=lon, camera=camera)
```

- [ ] **Step 5: Run tests again and confirm they pass**

```bash
pytest tests/test_exif.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add ingest/exif.py tests/test_exif.py tests/conftest.py
git commit -m "feat(ingest): add exif extraction with pillow"
```

---

## Task 4: Reverse geocoding with cache (TDD)

**Files:**
- Create: `tests/test_geocode.py`
- Create: `ingest/geocode.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_geocode.py`:

```python
"""Tests for the reverse geocoder.

We mock urlopen so tests don't hit Nominatim. The on-disk cache is exercised
by the cache_roundtrip test.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
from io import BytesIO

import pytest

from ingest import geocode


NOMINATIM_RESPONSE_PARIS = {
    "address": {
        "country": "France",
        "city": "Paris",
        "country_code": "fr",
    }
}


def _mock_urlopen(payload: dict):
    """Build a context-manager replacement for urlopen returning `payload`."""
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
    with patch("ingest.geocode.urlopen", _mock_urlopen(NOMINATIM_RESPONSE_PARIS)) as m:
        geocode.reverse(48.8566, 2.3522, cache_path=cache)
        # Second call should hit the cache, not the mock.
        geocode.reverse(48.8566, 2.3522, cache_path=cache)
    assert json.loads(cache.read_text())["48.8566,2.3522"] == {"country": "France", "city": "Paris"}


def test_reverse_falls_back_when_city_missing(tmp_path: Path):
    payload = {"address": {"country": "Iceland", "town": "Vík í Mýrdal"}}
    cache = tmp_path / "geocode.json"
    with patch("ingest.geocode.urlopen", _mock_urlopen(payload)):
        result = geocode.reverse(63.4, -19.0, cache_path=cache)
    # Nominatim sometimes returns `town` or `village` instead of `city`.
    assert result == ("Iceland", "Vík í Mýrdal")


def test_reverse_returns_none_when_country_missing(tmp_path: Path):
    payload = {"address": {}}
    cache = tmp_path / "geocode.json"
    with patch("ingest.geocode.urlopen", _mock_urlopen(payload)):
        result = geocode.reverse(0.0, 0.0, cache_path=cache)
    assert result is None
```

- [ ] **Step 2: Run the failing test**

```bash
pytest tests/test_geocode.py -v
```

Expected: import error.

- [ ] **Step 3: Implement `ingest/geocode.py`**

```python
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
    """Return (country, city) for the coordinates, or None if either is missing.

    Results are cached at `cache_path` (a JSON file). Repeated calls for the same
    rounded coordinate hit the cache.
    """
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_geocode.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add ingest/geocode.py tests/test_geocode.py
git commit -m "feat(ingest): add reverse geocode with on-disk cache"
```

---

## Task 5: Slug generation (TDD)

**Files:**
- Create: `tests/test_slug.py`
- Create: `ingest/slug.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_slug.py`:

```python
from datetime import datetime

from ingest import slug


def test_basic_slug_from_date_and_city():
    s = slug.build(datetime(2018, 7, 14), city="Paris", existing=set())
    assert s == "2018-07-14-paris"


def test_slug_normalizes_diacritics_and_spaces():
    s = slug.build(datetime(2021, 3, 8), city="São Paulo", existing=set())
    assert s == "2021-03-08-sao-paulo"


def test_slug_appends_suffix_on_collision():
    existing = {"2018-07-14-paris"}
    s = slug.build(datetime(2018, 7, 14), city="Paris", existing=existing)
    assert s == "2018-07-14-paris-2"


def test_slug_appends_increasing_suffix():
    existing = {"2018-07-14-paris", "2018-07-14-paris-2", "2018-07-14-paris-3"}
    s = slug.build(datetime(2018, 7, 14), city="Paris", existing=existing)
    assert s == "2018-07-14-paris-4"


def test_slug_handles_missing_city():
    s = slug.build(datetime(2018, 7, 14), city=None, existing=set())
    assert s == "2018-07-14"
```

- [ ] **Step 2: Run failing test**

```bash
pytest tests/test_slug.py -v
```

Expected: import error.

- [ ] **Step 3: Implement `ingest/slug.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_slug.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add ingest/slug.py tests/test_slug.py
git commit -m "feat(ingest): add slug builder with diacritic normalisation"
```

---

## Task 6: Front matter rendering (TDD)

**Files:**
- Create: `tests/test_frontmatter.py`
- Create: `ingest/frontmatter.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_frontmatter.py`:

```python
from datetime import datetime, timezone, timedelta

from ingest import frontmatter


def test_renders_full_front_matter():
    paris = timezone(timedelta(hours=2))
    md = frontmatter.render(
        title="",
        slug="paris-stencil-dog",
        date=datetime(2018, 7, 14, 16, 23, 0, tzinfo=paris),
        publish_date=datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc),
        photo="2018/07/paris-stencil-dog.jpg",
        country="France",
        city="Paris",
        camera="iPhone 7",
        lat=48.8566,
        lon=2.3522,
    )
    assert md.startswith("---\n")
    assert "slug: \"paris-stencil-dog\"" in md
    assert "date: 2018-07-14T16:23:00+02:00" in md
    assert "publishDate: 2026-05-15T10:00:00Z" in md
    assert "photo: 2018/07/paris-stencil-dog.jpg" in md
    assert "countries: [France]" in md
    assert "cities: [Paris]" in md
    assert "artists: []" in md
    assert "tags: []" in md
    assert "years: [2018]" in md
    assert "weight: 0" in md
    assert "camera: \"iPhone 7\"" in md
    assert "lat: 48.8566" in md
    assert "lon: 2.3522" in md
    assert md.endswith("---\n")


def test_renders_iso_date_in_utc():
    md = frontmatter.render(
        title="",
        slug="x",
        date=datetime(2018, 7, 14, 16, 23, 0, tzinfo=timezone.utc),
        publish_date=datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc),
        photo="x.jpg",
        country="France",
        city="Paris",
        camera="iPhone 7",
        lat=0.0,
        lon=0.0,
    )
    assert "date: 2018-07-14T16:23:00Z" in md


def test_render_quotes_camera_with_spaces():
    md = frontmatter.render(
        title="",
        slug="x",
        date=datetime(2020, 1, 1, tzinfo=timezone.utc),
        publish_date=datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc),
        photo="x.jpg",
        country="X",
        city="Y",
        camera="iPhone Pro Max 15",
        lat=0.0,
        lon=0.0,
    )
    assert 'camera: "iPhone Pro Max 15"' in md
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_frontmatter.py -v
```

Expected: import error.

- [ ] **Step 3: Implement `ingest/frontmatter.py`**

```python
"""Render Hugo front matter as a string.

We hand-write the YAML rather than using pyyaml so the field order is stable
and the output reads like the spec example exactly.
"""

from __future__ import annotations

from datetime import datetime, timezone


def _iso(dt: datetime) -> str:
    """Format datetime as RFC 3339 / ISO 8601 with `Z` for UTC, offset otherwise."""
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) == timezone.utc.utcoffset(dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")[:-2] + ":" + dt.strftime("%z")[-2:]


def render(
    *,
    title: str,
    slug: str,
    date: datetime,
    publish_date: datetime,
    photo: str,
    country: str,
    city: str,
    camera: str | None,
    lat: float,
    lon: float,
) -> str:
    lines = [
        "---",
        f'title: "{title}"',
        f'slug: "{slug}"',
        f"date: {_iso(date)}",
        f"publishDate: {_iso(publish_date)}",
        f"photo: {photo}",
        f"countries: [{country}]",
        f"cities: [{city}]",
        "artists: []",
        "tags: []",
        f"years: [{date.year}]",
        "weight: 0",
        "exif:",
        f'  camera: "{camera}"' if camera else '  camera: ""',
        f"  lat: {lat}",
        f"  lon: {lon}",
        "---",
        "",
    ]
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_frontmatter.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add ingest/frontmatter.py tests/test_frontmatter.py
git commit -m "feat(ingest): add front matter renderer"
```

---

## Task 7: Image resize (TDD)

**Files:**
- Create: `tests/test_resize.py`
- Create: `ingest/resize.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_resize.py`:

```python
from pathlib import Path

from PIL import Image

from ingest import resize


def test_to_web_resizes_long_edge_to_target(fixture_dir: Path, tmp_path: Path):
    src = fixture_dir / "with_gps.jpg"
    dst = tmp_path / "out.jpg"
    resize.to_web(src, dst, max_dim=80, quality=82)

    with Image.open(dst) as img:
        assert max(img.size) == 80
        assert img.format == "JPEG"


def test_to_web_does_not_upscale(fixture_dir: Path, tmp_path: Path):
    src = fixture_dir / "with_gps.jpg"  # 100x100 fixture
    dst = tmp_path / "out.jpg"
    resize.to_web(src, dst, max_dim=500, quality=82)

    with Image.open(dst) as img:
        assert max(img.size) == 100  # unchanged


def test_to_web_creates_parent_directories(fixture_dir: Path, tmp_path: Path):
    src = fixture_dir / "with_gps.jpg"
    dst = tmp_path / "nested" / "dir" / "out.jpg"
    resize.to_web(src, dst, max_dim=80, quality=82)
    assert dst.exists()
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_resize.py -v
```

Expected: import error.

- [ ] **Step 3: Implement `ingest/resize.py`**

```python
"""Resize a JPEG to a web-friendly size, preserving aspect ratio.

Never upscales — if the source is already smaller than max_dim, it's copied
through unchanged (still re-encoded at the target quality).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def to_web(src: Path, dst: Path, *, max_dim: int, quality: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = img.convert("RGB")
        long_edge = max(img.size)
        if long_edge > max_dim:
            scale = max_dim / long_edge
            new_size = (round(img.size[0] * scale), round(img.size[1] * scale))
            img = img.resize(new_size, Image.LANCZOS)
        img.save(dst, format="JPEG", quality=quality, optimize=True, progressive=True)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_resize.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add ingest/resize.py tests/test_resize.py
git commit -m "feat(ingest): add jpeg resize with aspect preservation"
```

---

## Task 8: Pipeline orchestration (TDD)

**Files:**
- Create: `tests/test_pipeline.py`
- Create: `ingest/pipeline.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_pipeline.py`:

```python
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from ingest import pipeline


def test_process_writes_post_and_image(fixture_dir: Path, tmp_path: Path):
    content_root = tmp_path / "content" / "posts"
    asset_root = tmp_path / "assets" / "img"
    cache = tmp_path / "geocode.json"

    publish_date = datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc)

    with patch("ingest.pipeline.reverse_geocode", return_value=("France", "Paris")):
        result = pipeline.process(
            source=fixture_dir / "with_gps.jpg",
            content_root=content_root,
            asset_root=asset_root,
            existing_slugs=set(),
            publish_date=publish_date,
            cache_path=cache,
        )

    assert result.status == "ok"
    assert result.slug == "2018-07-14-paris"

    md_path = content_root / "2018-07-14-paris.md"
    assert md_path.exists()
    md = md_path.read_text()
    assert 'slug: "2018-07-14-paris"' in md
    assert "countries: [France]" in md
    assert "cities: [Paris]" in md
    assert "photo: 2018/07/2018-07-14-paris.jpg" in md
    assert 'camera: "iPhone 7"' in md

    img_path = asset_root / "2018" / "07" / "2018-07-14-paris.jpg"
    assert img_path.exists()


def test_process_returns_skip_when_gps_missing(fixture_dir: Path, tmp_path: Path):
    content_root = tmp_path / "content" / "posts"
    asset_root = tmp_path / "assets" / "img"
    cache = tmp_path / "geocode.json"

    result = pipeline.process(
        source=fixture_dir / "no_gps.jpg",
        content_root=content_root,
        asset_root=asset_root,
        existing_slugs=set(),
        publish_date=datetime(2026, 5, 15, tzinfo=timezone.utc),
        cache_path=cache,
    )

    assert result.status == "skip"
    assert "gps" in result.reason.lower()
    # No outputs written.
    assert list(content_root.rglob("*.md")) == []


def test_process_returns_skip_when_no_exif(fixture_dir: Path, tmp_path: Path):
    content_root = tmp_path / "content" / "posts"
    asset_root = tmp_path / "assets" / "img"
    cache = tmp_path / "geocode.json"

    result = pipeline.process(
        source=fixture_dir / "no_exif.jpg",
        content_root=content_root,
        asset_root=asset_root,
        existing_slugs=set(),
        publish_date=datetime(2026, 5, 15, tzinfo=timezone.utc),
        cache_path=cache,
    )

    assert result.status == "skip"
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_pipeline.py -v
```

Expected: import error.

- [ ] **Step 3: Implement `ingest/pipeline.py`**

```python
"""Orchestrate one photo: extract EXIF, geocode, resize, write markdown.

A `Result` says what happened: ok, skip (with reason), or error (with detail).
The caller decides what to do with skip/error — typically log them and move on.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from ingest import exif, frontmatter, resize, slug
from ingest.geocode import reverse as reverse_geocode


WEB_MAX_DIM = 1600
WEB_QUALITY = 82


@dataclass(frozen=True)
class Result:
    status: str         # "ok" | "skip" | "error"
    source: Path
    slug: Optional[str] = None
    reason: str = ""


def process(
    *,
    source: Path,
    content_root: Path,
    asset_root: Path,
    existing_slugs: Iterable[str],
    publish_date: datetime,
    cache_path: Path,
) -> Result:
    data = exif.extract(source)
    if data is None or data.date is None:
        return Result("skip", source, reason="missing exif date")
    if data.lat is None or data.lon is None:
        return Result("skip", source, reason="missing gps coordinates")

    place = reverse_geocode(data.lat, data.lon, cache_path=cache_path)
    if place is None:
        return Result("skip", source, reason="reverse-geocode returned no country/city")
    country, city = place

    new_slug = slug.build(data.date, city=city, existing=existing_slugs)
    rel_photo = f"{data.date.year:04d}/{data.date.month:02d}/{new_slug}.jpg"

    img_dst = asset_root / rel_photo
    resize.to_web(source, img_dst, max_dim=WEB_MAX_DIM, quality=WEB_QUALITY)

    md = frontmatter.render(
        title="",
        slug=new_slug,
        date=data.date,
        publish_date=publish_date,
        photo=rel_photo,
        country=country,
        city=city,
        camera=data.camera,
        lat=round(data.lat, 4),
        lon=round(data.lon, 4),
    )
    md_path = content_root / f"{new_slug}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md)

    return Result("ok", source, slug=new_slug)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_pipeline.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add ingest/pipeline.py tests/test_pipeline.py
git commit -m "feat(ingest): add per-photo pipeline orchestration"
```

---

## Task 9: CLI entry point and end-to-end run

**Files:**
- Create: `ingest/__main__.py`

- [ ] **Step 1: Implement the CLI**

Create `ingest/__main__.py`:

```python
"""Command-line entry: process every photo under _ingest/.

Usage:
    python -m ingest [--ingest DIR] [--dry-run]

Behavior:
- Scans `_ingest/` (default) for .jpg/.jpeg/.JPG/.JPEG files (recursively).
- Skips files inside `_ingest/_processed/`.
- For each photo, runs the pipeline.
- On success: moves the original to `_ingest/_processed/`.
- On skip: appends a line to `_ingest/_missing-location.log`.
- Prints a summary at the end.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from ingest import pipeline


def _gather_existing_slugs(content_root: Path) -> set[str]:
    return {p.stem for p in content_root.glob("*.md") if p.stem != "_index"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ingest")
    parser.add_argument("--ingest", type=Path, default=Path("_ingest"),
                        help="Directory containing original photos (default: _ingest)")
    parser.add_argument("--content", type=Path, default=Path("content/posts"),
                        help="Hugo content output dir (default: content/posts)")
    parser.add_argument("--assets", type=Path, default=Path("assets/img"),
                        help="Hugo asset output dir (default: assets/img)")
    parser.add_argument("--cache", type=Path, default=Path(".cache/geocode.json"),
                        help="Geocode cache file (default: .cache/geocode.json)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Process but do not move originals to _processed/")
    args = parser.parse_args(argv)

    ingest_dir: Path = args.ingest
    processed_dir = ingest_dir / "_processed"
    log_path = ingest_dir / "_missing-location.log"

    if not ingest_dir.exists():
        print(f"error: {ingest_dir} does not exist", file=sys.stderr)
        return 2

    sources = [
        p for p in ingest_dir.rglob("*")
        if p.is_file()
        and p.suffix.lower() in {".jpg", ".jpeg"}
        and processed_dir not in p.parents
    ]
    if not sources:
        print(f"no .jpg/.jpeg files found under {ingest_dir}")
        return 0

    existing_slugs = _gather_existing_slugs(args.content)
    publish_date = datetime.now(timezone.utc).replace(microsecond=0)

    ok = skip = err = 0
    for src in sorted(sources):
        result = pipeline.process(
            source=src,
            content_root=args.content,
            asset_root=args.assets,
            existing_slugs=existing_slugs,
            publish_date=publish_date,
            cache_path=args.cache,
        )
        if result.status == "ok":
            ok += 1
            existing_slugs.add(result.slug)
            if not args.dry_run:
                processed_dir.mkdir(parents=True, exist_ok=True)
                src.rename(processed_dir / src.name)
            print(f"  ok    {src.name} -> {result.slug}")
        elif result.status == "skip":
            skip += 1
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a") as f:
                f.write(f"{datetime.now().isoformat()}\t{src}\t{result.reason}\n")
            print(f"  skip  {src.name} ({result.reason})")
        else:
            err += 1
            print(f"  ERROR {src.name}: {result.reason}", file=sys.stderr)

    print(f"\ndone: {ok} processed, {skip} skipped, {err} errors")
    return 0 if err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Manual end-to-end test**

```bash
mkdir -p _ingest
cp tests/fixtures/with_gps.jpg _ingest/test-paris.jpg
cp tests/fixtures/no_gps.jpg _ingest/test-nogps.jpg
python -m ingest --dry-run
```

Expected output (the geocode call will hit Nominatim — needs internet):

```
  ok    test-paris.jpg -> 2018-07-14-paris
  skip  test-nogps.jpg (missing gps coordinates)

done: 1 processed, 1 skipped, 0 errors
```

Verify the new files:

```bash
ls content/posts/2018-07-14-paris.md assets/img/2018/07/2018-07-14-paris.jpg
cat content/posts/2018-07-14-paris.md
```

Then **clean up** before committing — these were test artifacts:

```bash
rm content/posts/2018-07-14-paris.md
rm assets/img/2018/07/2018-07-14-paris.jpg
rm _ingest/test-paris.jpg _ingest/test-nogps.jpg _ingest/_missing-location.log
rmdir _ingest 2>/dev/null || true
```

- [ ] **Step 3: Commit**

```bash
git add ingest/__main__.py
git commit -m "feat(ingest): add cli entry with dry-run and skip-logging"
```

---

## Task 10: README for the ingest workflow

**Files:**
- Create: `ingest/README.md`

- [ ] **Step 1: Document the workflow**

Create `ingest/README.md`:

```markdown
# Ingest

Turn original smartphone photos into Hugo posts.

## Setup (once)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

1. Drop original JPEGs into `_ingest/` (any folder structure within it is fine).
2. Activate the venv: `source .venv/bin/activate`
3. Run: `python -m ingest`
4. Each photo with date + GPS EXIF produces:
   - `content/posts/YYYY-MM-DD-<city>.md` — front matter prefilled, `title:`, `tags:`, `artists:` blank for you to fill in
   - `assets/img/YYYY/MM/YYYY-MM-DD-<city>.jpg` — web-sized (1600px long edge, q82)
5. Successfully processed originals move to `_ingest/_processed/`. Failures (no GPS, no EXIF date) log to `_ingest/_missing-location.log` and the original stays put.

Use `--dry-run` to process without moving originals.

## Notes

- Reverse geocoding uses OpenStreetMap Nominatim. First lookup for a given coordinate hits the network; subsequent lookups within ~10m hit the cache at `.cache/geocode.json`.
- City names come from Nominatim's `city` → `town` → `village` → `hamlet` → `suburb` → `municipality` fallback chain. If none of those exist, the photo is skipped.
- After ingest, manually fill in `tags:`, `artists:`, optional `title:`, and commentary in the body of each generated markdown file before publishing.

## Tests

```bash
pytest
```

Test fixtures are auto-generated in `tests/fixtures/` at the start of each session.
```

- [ ] **Step 2: Commit**

```bash
git add ingest/README.md
git commit -m "docs(ingest): add ingest workflow readme"
```

---

## Self-review notes (for the author)

**Spec coverage:**

| Spec requirement | Task |
|---|---|
| Read EXIF (date, GPS, camera) | 3 |
| Reverse-geocode GPS → country/city | 4 |
| Generate slug from date + city | 5 |
| Output front matter matching the content model | 6 |
| Resize JPEG to web-sized | 7 |
| Move original to `_processed/` after success | 9 |
| Log photos missing GPS or date | 9 |
| Tags lowercased, country/city title-cased | Inherent: Nominatim returns title-case country/city; the ingest outputs them verbatim. Tags are blank by default — the user fills in. |
| Skip photo without GPS, don't process | 8 (Result with `status=skip`) |
| Cache geocode responses | 4 |
| Idempotent on re-run | 9 (originals move out of `_ingest/`, so the next run sees nothing) |
| All Python deps via venv | 1, 2 |

**Deliberately deferred:**

- Sidecar `.yaml` for manually supplying missing EXIF — not implemented. If a photo lacks GPS or date, the user adds it via a photo metadata editor or generates the markdown by hand.
- City disambiguation across countries (e.g., Paris FR vs Paris TX). The spec accepted this risk.
- Concurrent processing. With ≤200 photos and Nominatim's 1 req/sec policy, serial is fine.
- Custom alt text generation. The script leaves `alt` unset (Plan A's `photo.html` partial defaults it to empty) — user fills in during editorial pass.

**What's next:**

Plan A's Hugo site renders any post the ingest script produces, with no further site changes needed. Drop real photos in `_ingest/`, run `python -m ingest`, fill in tags/artists/commentary, and the post appears at `/<year>/<month>/<slug>/`.
