#!/usr/bin/env python3
"""Audit photo-post descriptions against the amendment spec.

Reports, for every post in content/posts/*.md:
  - description begins with "Photo of" (allowed only as fallback; flag for review)
  - description length > 160 chars
  - description missing the post's year (date.year)
  - description ends with ", in <City>." where <City> is already in title
  - title ends with a neighbourhood-like trailing token not in cities/countries
    (heuristic: trailing token after the last comma not equal to any cities[] entry)

Exit non-zero if any HARD violations (length, missing year) are present.
Soft warnings ("Photo of", trailing-city, neighbourhood) are printed but don't fail.
"""
from __future__ import annotations
import re, sys, pathlib

POSTS = pathlib.Path("content/posts")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def parse_front_matter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm


def strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        s = s[1:-1]
    return s.replace('\\"', '"')


def parse_list(s: str) -> list[str]:
    s = s.strip().lstrip("[").rstrip("]")
    if not s:
        return []
    return [item.strip().strip('"').strip("'") for item in s.split(",")]


def year_from_date(date_str: str) -> str | None:
    m = re.match(r"(\d{4})", date_str.strip())
    return m.group(1) if m else None


def audit_post(path: pathlib.Path) -> tuple[list[str], list[str]]:
    text = path.read_text()
    fm = parse_front_matter(text)
    title = strip_quotes(fm.get("title", ""))
    desc = strip_quotes(fm.get("description", ""))
    cities = parse_list(fm.get("cities", "[]"))
    year = year_from_date(fm.get("date", ""))

    hard, soft = [], []
    if len(desc) > 160:
        hard.append(f"description length {len(desc)} > 160")
    if year and year not in desc:
        hard.append(f"description missing year {year}")
    if desc.lower().startswith("photo of"):
        soft.append("description starts with 'Photo of' (fallback only)")
    for city in cities:
        if city and f", in {city}." in desc and city in title:
            soft.append(f"description ends with city '{city}' already in title")
    if "," in title:
        trailing = title.rsplit(",", 1)[1].strip()
        if (
            trailing
            and trailing not in cities
            and trailing not in parse_list(fm.get("countries", "[]"))
        ):
            soft.append(
                f"title ends with '{trailing}' (not in cities/countries — neighbourhood?)"
            )
    return hard, soft


def main() -> int:
    exit_code = 0
    posts = sorted(p for p in POSTS.glob("*.md") if p.name != "_index.md")
    for p in posts:
        hard, soft = audit_post(p)
        if hard or soft:
            print(f"\n{p}")
            for h in hard:
                print(f"  HARD: {h}")
                exit_code = 1
            for s in soft:
                print(f"  soft: {s}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
