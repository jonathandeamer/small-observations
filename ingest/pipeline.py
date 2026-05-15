"""Orchestrate one photo: extract EXIF, geocode, resize, write markdown.

A `Result` says what happened: ok, skip (with reason), or error (with detail).
The caller decides what to do with skip/error — typically log them and move on.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from ingest import exif, frontmatter, resize, slug
from ingest.geocode import reverse as reverse_geocode


WEB_MAX_DIM = 1600
WEB_QUALITY = 82


@dataclass(frozen=True)
class Result:
    status: str         # "ok" | "skip" | "error"
    source: Path
    slug: Optional[str] = None
    reason: str = ""


def process(
    *,
    source: Path,
    content_root: Path,
    asset_root: Path,
    existing_slugs: Iterable[str],
    publish_date: datetime,
    cache_path: Path,
) -> Result:
    data = exif.extract(source)
    if data is None or data.date is None:
        return Result("skip", source, reason="missing exif date")

    country: Optional[str] = None
    city: Optional[str] = None
    if data.lat is not None and data.lon is not None:
        place = reverse_geocode(data.lat, data.lon, cache_path=cache_path)
        if place is not None:
            country, city = place

    new_slug = slug.build(data.date, city=city, existing=existing_slugs)
    rel_photo = f"{data.date.year:04d}/{data.date.month:02d}/{new_slug}.jpg"

    img_dst = asset_root / rel_photo
    resize.to_web(source, img_dst, max_dim=WEB_MAX_DIM, quality=WEB_QUALITY)

    md = frontmatter.render(
        title="",
        slug=new_slug,
        date=data.date,
        publish_date=publish_date,
        photo=rel_photo,
        country=country,
        city=city,
        camera=data.camera,
        lat=round(data.lat, 4) if data.lat is not None else None,
        lon=round(data.lon, 4) if data.lon is not None else None,
    )
    md_path = content_root / f"{new_slug}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md)

    return Result("ok", source, slug=new_slug)
