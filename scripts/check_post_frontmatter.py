#!/usr/bin/env python3
"""Check source photo-post front matter for required editorial fields."""

from __future__ import annotations

import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
DATE_YEAR_RE = re.compile(r"^(\d{4})-")

REQUIRED_KEYS = [
    "slug",
    "date",
    "publishDate",
    "photo",
    "title",
    "description",
    "alt",
    "countries",
    "cities",
    "artists",
    "tags",
    "years",
    "weight",
    "exif",
]
NON_EMPTY_KEYS = ["slug", "date", "publishDate", "photo", "title", "description", "alt"]
INLINE_LIST_KEYS = ["countries", "cities", "artists", "tags", "years"]


def parse_front_matter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}

    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line or line.startswith(" "):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip()
    return frontmatter


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value.replace('\\"', '"').strip()


def is_inline_list(value: str) -> bool:
    value = value.strip()
    return value.startswith("[") and value.endswith("]")


def list_values(value: str) -> list[str]:
    value = value.strip()[1:-1].strip()
    if not value:
        return []
    return [strip_quotes(item.strip()) for item in value.split(",")]


def audit_post(path: Path) -> list[str]:
    frontmatter = parse_front_matter(path.read_text())
    label = path.name
    errors: list[str] = []

    for key in REQUIRED_KEYS:
        if key not in frontmatter:
            errors.append(f"{label}: missing required key '{key}'")

    for key in NON_EMPTY_KEYS:
        if key in frontmatter and not strip_quotes(frontmatter[key]):
            errors.append(f"{label}: '{key}' must be non-empty")

    for key in INLINE_LIST_KEYS:
        if key in frontmatter and not is_inline_list(frontmatter[key]):
            errors.append(f"{label}: '{key}' must be an inline list")

    if "date" in frontmatter and "years" in frontmatter and is_inline_list(frontmatter["years"]):
        year_match = DATE_YEAR_RE.match(strip_quotes(frontmatter["date"]))
        if year_match and year_match.group(1) not in list_values(frontmatter["years"]):
            errors.append(f"{label}: 'years' must include date year {year_match.group(1)}")

    return errors


def audit_posts(posts_dir: Path) -> list[str]:
    posts = sorted(path for path in posts_dir.glob("*.md") if path.name != "_index.md")
    errors: list[str] = []
    for path in posts:
        errors.extend(audit_post(path))
    return errors


def main(argv: list[str]) -> int:
    posts_dir = Path(argv[1]) if len(argv) > 1 else Path("content/posts")
    errors = audit_posts(posts_dir)
    if not errors:
        print("    ok")
        return 0
    for error in errors[:40]:
        print(f"    {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
