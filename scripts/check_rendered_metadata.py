#!/usr/bin/env python3
"""Check rendered post pages for required metadata tags."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path


class MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.canonical = ""
        self.rss = ""
        self.meta: dict[tuple[str, str], str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {name.lower(): value or "" for name, value in attrs}
        if tag == "title":
            self.in_title = True
            return
        if tag == "link":
            rels = {part.lower() for part in attr_map.get("rel", "").split()}
            if "canonical" in rels:
                self.canonical = attr_map.get("href", "").strip()
            if "alternate" in rels and attr_map.get("type") == "application/rss+xml":
                self.rss = attr_map.get("href", "").strip()
            return
        if tag == "meta":
            content = attr_map.get("content", "").strip()
            if "property" in attr_map:
                self.meta[("property", attr_map["property"])] = content
            if "name" in attr_map:
                self.meta[("name", attr_map["name"])] = content

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return "".join(self.title_parts).strip()


def post_pages(public_dir: Path) -> list[Path]:
    return sorted(public_dir.glob("[0-9]*/*/*/index.html"))


def audit_page(path: Path, public_dir: Path) -> list[str]:
    parser = MetadataParser()
    parser.feed(path.read_text())
    label = path.relative_to(public_dir).as_posix()
    errors: list[str] = []

    if not parser.title:
        errors.append(f"{label}: missing non-empty <title>")
    if not parser.canonical:
        errors.append(f"{label}: missing non-empty canonical link")
    if not parser.rss:
        errors.append(f"{label}: missing RSS autodiscovery link")

    checks = [
        (("property", "og:title"), "og:title"),
        (("property", "og:description"), "og:description"),
        (("property", "og:image"), "og:image"),
        (("name", "twitter:card"), "twitter:card"),
    ]
    for key, label_name in checks:
        if not parser.meta.get(key, "").strip():
            errors.append(f"{label}: missing non-empty {label_name}")

    return errors


def audit_rendered_posts(public_dir: Path) -> list[str]:
    errors: list[str] = []
    for path in post_pages(public_dir):
        errors.extend(audit_page(path, public_dir))
    return errors


def main(argv: list[str]) -> int:
    public_dir = Path(argv[1]) if len(argv) > 1 else Path("public")
    errors = audit_rendered_posts(public_dir)
    if not errors:
        print("    ok")
        return 0
    for error in errors[:40]:
        print(f"    {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
