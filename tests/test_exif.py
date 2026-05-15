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
