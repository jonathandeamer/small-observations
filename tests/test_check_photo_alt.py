from pathlib import Path

from scripts.check_photo_alt import find_pages_with_empty_photo_alt


def write_page(path: Path, img: str) -> None:
    path.parent.mkdir(parents=True)
    path.write_text(f"<!doctype html><html><body>{img}</body></html>")


def test_accepts_double_and_single_quoted_alt_text(tmp_path: Path) -> None:
    double_quoted = tmp_path / "public/2024/01/double/index.html"
    single_quoted = tmp_path / "public/2024/01/single/index.html"
    write_page(double_quoted, '<img src="/photo.jpg" alt="Plain description">')
    write_page(single_quoted, "<img src=\"/photo.jpg\" alt='Description with \"quoted\" text'>")

    assert find_pages_with_empty_photo_alt(tmp_path / "public") == []


def test_reports_missing_and_empty_alt_text(tmp_path: Path) -> None:
    missing = tmp_path / "public/2024/01/missing/index.html"
    empty = tmp_path / "public/2024/01/empty/index.html"
    whitespace = tmp_path / "public/2024/01/whitespace/index.html"
    write_page(missing, '<img src="/photo.jpg">')
    write_page(empty, '<img src="/photo.jpg" alt="">')
    write_page(whitespace, '<img src="/photo.jpg" alt="   ">')

    assert set(find_pages_with_empty_photo_alt(tmp_path / "public")) == {
        missing,
        empty,
        whitespace,
    }
