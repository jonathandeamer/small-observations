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
