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
