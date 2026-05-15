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
    assert 'slug: "paris-stencil-dog"' in md
    assert "date: 2018-07-14T16:23:00+02:00" in md
    assert "publishDate: 2026-05-15T10:00:00Z" in md
    assert "photo: 2018/07/paris-stencil-dog.jpg" in md
    assert "countries: [France]" in md
    assert "cities: [Paris]" in md
    assert "artists: []" in md
    assert "tags: []" in md
    assert "years: [2018]" in md
    assert "weight: 0" in md
    assert 'camera: "iPhone 7"' in md
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
