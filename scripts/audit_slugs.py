#!/usr/bin/env python3
"""Audit photo-post slugs against the bootstrap spec.

Reports, for every post in content/posts/*.md:
  HARD violations (script exits non-zero):
    - slug missing
    - slug contains characters outside [a-z0-9-]
    - slug has leading/trailing hyphen or double hyphen
    - slug exceeds 70 characters
    - slug collides with another post in the same year+month bucket
    - hook token is not grounded in this post's title/alt/tags/artists
      (catches misapplied slugs — wrong slug in wrong file)
  Soft warnings (printed, exit stays 0):
    - slug does not start with the expected city prefix
    - slug is the legacy YYYY-MM-DD-<city> shape (not yet rewritten)
"""
from __future__ import annotations
import re, sys, pathlib, unicodedata
from collections import defaultdict

POSTS = pathlib.Path("content/posts")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
SLUG_CHARSET_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LEGACY_SHAPE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}($|-)")

# Maps cities[] value to expected slug prefix. Mirrors the spec table.
CITY_PREFIXES = {
    "Greater London": "london",
    "Basingstoke and Deane": "basingstoke",
    "Reykjavikurborg": "reykjavik",
    "Derbyshire Dales": "derbyshire-dales",
    "Mountain View": "mountain-view",
    "Penrhyndeudraeth": "penrhyndeudraeth",
    "Bucharest": "bucharest",
    "New York": "new-york",
    "San Francisco": "san-francisco",
}


def kebab(s: str) -> str:
    return s.lower().replace(" ", "-")


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


def expected_prefix(cities: list[str]) -> str | None:
    if not cities:
        return None
    city = cities[0]
    return CITY_PREFIXES.get(city, kebab(city))


def normalize(s: str) -> str:
    """Lowercase, strip diacritics, keep only [a-z0-9]."""
    nfkd = unicodedata.normalize("NFKD", s.lower())
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", ascii_only)


def grounding_corpus(fm: dict) -> str:
    """One big normalized string of every field a slug hook may draw from."""
    parts = [
        strip_quotes(fm.get("title", "")),
        strip_quotes(fm.get("alt", "")),
    ]
    parts.extend(parse_list(fm.get("tags", "[]")))
    parts.extend(parse_list(fm.get("artists", "[]")))
    return normalize(" ".join(parts))


def check_grounding(slug: str, prefix: str | None, fm: dict) -> list[str]:
    """For each hook token (after the city prefix), verify it appears in the
    post's own grounding fields. Catches the wrong-slug-wrong-file class of
    misapplication: e.g. `seville-kurt-cobain` applied to the Dublin file
    fails because `kurt` and `cobain` are not substrings of Dublin's fields."""
    hook = slug
    if prefix and (slug == prefix or slug.startswith(prefix + "-")):
        hook = slug[len(prefix):].lstrip("-")
    if not hook:
        return []
    corpus = grounding_corpus(fm)
    failures: list[str] = []
    for token in hook.split("-"):
        if not token:
            continue
        if normalize(token) not in corpus:
            failures.append(f"hook token '{token}' not grounded in title/alt/tags/artists")
    return failures


def year_month_from_date(date_str: str) -> str | None:
    m = re.match(r"(\d{4})-(\d{2})", date_str.strip())
    return f"{m.group(1)}-{m.group(2)}" if m else None


def audit_post(path: pathlib.Path) -> tuple[list[str], list[str], str | None, str | None]:
    text = path.read_text()
    fm = parse_front_matter(text)
    slug = strip_quotes(fm.get("slug", ""))
    cities = parse_list(fm.get("cities", "[]"))
    ym = year_month_from_date(fm.get("date", ""))

    hard, soft = [], []
    if not slug:
        hard.append("slug missing")
        return hard, soft, ym, slug
    if not SLUG_CHARSET_RE.match(slug):
        hard.append(f"slug '{slug}' violates [a-z0-9-]+ shape")
    if len(slug) > 70:
        hard.append(f"slug length {len(slug)} > 70")
    if LEGACY_SHAPE_RE.match(slug):
        soft.append(f"slug '{slug}' is the legacy YYYY-MM-DD-<city> shape (not yet rewritten)")
    else:
        prefix = expected_prefix(cities)
        if prefix and not slug.startswith(prefix + "-") and slug != prefix:
            soft.append(f"slug '{slug}' does not start with expected city prefix '{prefix}'")
        hard.extend(check_grounding(slug, prefix, fm))
    return hard, soft, ym, slug


def main() -> int:
    exit_code = 0
    posts = sorted(p for p in POSTS.glob("*.md") if p.name != "_index.md")
    by_bucket: dict[str, list[tuple[str, pathlib.Path]]] = defaultdict(list)

    for p in posts:
        hard, soft, ym, slug = audit_post(p)
        if hard or soft:
            print(f"\n{p}")
            for h in hard:
                print(f"  HARD: {h}")
                exit_code = 1
            for s in soft:
                print(f"  soft: {s}")
        if ym and slug:
            by_bucket[ym].append((slug, p))

    # Collision check within each year-month bucket.
    for ym, entries in by_bucket.items():
        seen: dict[str, pathlib.Path] = {}
        for slug, p in entries:
            if slug in seen:
                print(f"\nHARD: slug '{slug}' in {ym} collides:")
                print(f"  - {seen[slug]}")
                print(f"  - {p}")
                exit_code = 1
            else:
                seen[slug] = p

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
