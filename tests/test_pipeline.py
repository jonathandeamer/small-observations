from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

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
