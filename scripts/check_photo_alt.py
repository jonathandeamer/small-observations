#!/usr/bin/env python3
"""Check rendered post photos for missing or empty alt text."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path


class ImgAltParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.has_empty_photo_alt = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        attr_map = {name.lower(): value for name, value in attrs}
        alt = attr_map.get("alt")
        if alt is None or not alt.strip():
            self.has_empty_photo_alt = True


def post_pages(public_dir: Path) -> list[Path]:
    return sorted(public_dir.glob("[0-9]*/*/*/index.html"))


def page_has_empty_photo_alt(path: Path) -> bool:
    parser = ImgAltParser()
    parser.feed(path.read_text())
    return parser.has_empty_photo_alt


def find_pages_with_empty_photo_alt(public_dir: Path) -> list[Path]:
    return [path for path in post_pages(public_dir) if page_has_empty_photo_alt(path)]


def main(argv: list[str]) -> int:
    public_dir = Path(argv[1]) if len(argv) > 1 else Path("public")
    offenders = find_pages_with_empty_photo_alt(public_dir)
    if not offenders:
        print("    (none)")
        return 0
    for path in offenders[:20]:
        print(f"    {path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
