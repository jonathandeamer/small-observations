"""Render Hugo front matter as a string.

We hand-write the YAML rather than using pyyaml so the field order is stable
and the output reads like the spec example exactly.
"""

from __future__ import annotations

from datetime import datetime, timezone


def _iso(dt: datetime) -> str:
    """Format datetime as RFC 3339 / ISO 8601 with `Z` for UTC, offset otherwise."""
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) == timezone.utc.utcoffset(dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    base = dt.strftime("%Y-%m-%dT%H:%M:%S")
    off = dt.strftime("%z")  # like '+0200' or '-0500'
    return f"{base}{off[:3]}:{off[3:]}"


def render(
    *,
    title: str,
    slug: str,
    date: datetime,
    publish_date: datetime,
    photo: str,
    country: str | None,
    city: str | None,
    camera: str | None,
    lat: float | None,
    lon: float | None,
) -> str:
    lines = [
        "---",
        f'title: "{title}"',
        f'slug: "{slug}"',
        f"date: {_iso(date)}",
        f"publishDate: {_iso(publish_date)}",
        f"photo: {photo}",
        f"countries: [{country}]" if country else "countries: []",
        f"cities: [{city}]" if city else "cities: []",
        "artists: []",
        "tags: []",
        f"years: [{date.year}]",
        "weight: 0",
        "exif:",
        f'  camera: "{camera}"' if camera else '  camera: ""',
    ]
    if lat is not None:
        lines.append(f"  lat: {lat}")
    if lon is not None:
        lines.append(f"  lon: {lon}")
    lines.extend(["---", ""])
    return "\n".join(lines)
