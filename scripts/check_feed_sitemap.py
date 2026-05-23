#!/usr/bin/env python3
"""Check rendered RSS and sitemap URL contracts."""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

SITE = "https://smallobservations.net"
FEED_URL = f"{SITE}/feed.xml"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
ATOM_NS = "{http://www.w3.org/2005/Atom}"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
MAX_RSS_ITEMS = 20


class FeedContentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.image_src = ""
        self.image_alt = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "img" or self.image_src:
            return
        attr_map = {name: value or "" for name, value in attrs}
        self.image_src = attr_map.get("src", "").strip()
        self.image_alt = attr_map.get("alt", "").strip()


def parse_front_matter(path: Path) -> dict[str, str]:
    match = FRONTMATTER_RE.match(path.read_text())
    if not match:
        return {}
    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line or line.startswith(" "):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip().strip('"')
    return frontmatter


def expected_post_urls(posts_dir: Path) -> dict[str, str]:
    urls: dict[str, str] = {}
    for path in sorted(p for p in posts_dir.glob("*.md") if p.name != "_index.md"):
        fm = parse_front_matter(path)
        date = fm.get("date", "")
        slug = fm.get("slug", "")
        publish_date = fm.get("publishDate", "")
        if len(date) < 7 or not slug or len(publish_date) < 19:
            continue
        url = f"{SITE}/{date[:4]}/{date[5:7]}/{slug}/"
        urls[url] = f"{publish_date[:19]}+00:00"
    return urls


def rss_items(feed: ET.Element) -> list[ET.Element]:
    channel = feed.find("channel")
    if channel is None:
        return []
    return list(channel.findall("item"))


def rss_item_link(item: ET.Element) -> str:
    return (item.findtext("link") or "").strip()


def rss_pub_date(item: ET.Element) -> datetime | None:
    value = (item.findtext("pubDate") or "").strip()
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


def rss_content_image(item: ET.Element) -> FeedContentParser:
    parser = FeedContentParser()
    content = item.findtext(f"{CONTENT_NS}encoded") or ""
    parser.feed(content)
    return parser


def rss_self_link(feed: ET.Element) -> str:
    channel = feed.find("channel")
    if channel is None:
        return ""
    for link in channel.findall(f"{ATOM_NS}link"):
        if link.attrib.get("rel") == "self":
            return link.attrib.get("href", "").strip()
    return ""


def rss_contact_errors(feed: ET.Element) -> list[str]:
    channel = feed.find("channel")
    if channel is None:
        return []
    errors: list[str] = []
    for tag in ("managingEditor", "webMaster"):
        value = (channel.findtext(tag) or "").strip()
        if value and "@" not in value:
            errors.append(f"feed.xml: {tag} must be omitted or contain an email address")
    return errors


def sitemap_entries(sitemap: ET.Element) -> dict[str, str]:
    entries: dict[str, str] = {}
    for url in sitemap.findall("sm:url", SITEMAP_NS):
        loc = url.findtext("sm:loc", default="", namespaces=SITEMAP_NS).strip()
        lastmod = url.findtext("sm:lastmod", default="", namespaces=SITEMAP_NS).strip()
        if loc:
            entries[loc] = lastmod
    return entries


def audit_feed_and_sitemap(public_dir: Path, posts_dir: Path) -> list[str]:
    errors: list[str] = []
    expected_urls = expected_post_urls(posts_dir)

    feed = ET.parse(public_dir / "feed.xml").getroot()
    self_link = rss_self_link(feed)
    if self_link != FEED_URL:
        errors.append(f"feed.xml: atom self link must be {FEED_URL}")
    errors.extend(rss_contact_errors(feed))

    items = rss_items(feed)
    if len(items) > MAX_RSS_ITEMS:
        errors.append(f"feed.xml: RSS feed must contain no more than {MAX_RSS_ITEMS} items")

    pub_dates = [rss_pub_date(item) for item in items]
    if any(pub_date is None for pub_date in pub_dates):
        errors.append("feed.xml: every RSS item must have a valid pubDate")
    elif pub_dates != sorted(pub_dates, reverse=True):
        errors.append("feed.xml: RSS items must be ordered by pubDate descending")

    for item in items:
        link = rss_item_link(item)
        if link not in expected_urls:
            errors.append(f"feed.xml: RSS item is not a photo post: {link}")
            continue
        image = rss_content_image(item)
        if not image.image_src:
            errors.append(f"feed.xml: {link} content must include an image")
            continue
        if not image.image_src.startswith(f"{SITE}/"):
            errors.append(f"feed.xml: {link} content image src must be absolute")
        if not image.image_alt:
            errors.append(f"feed.xml: {link} content image must have non-empty alt text")

    sitemap = ET.parse(public_dir / "sitemap.xml").getroot()
    entries = sitemap_entries(sitemap)
    not_found_url = f"{SITE}/404/"
    if not_found_url in entries:
        errors.append(f"sitemap.xml: must not include {not_found_url}")

    for url, expected_lastmod in expected_urls.items():
        actual_lastmod = entries.get(url)
        if actual_lastmod and actual_lastmod != expected_lastmod:
            errors.append(
                f"sitemap.xml: {url} lastmod {actual_lastmod} should use publishDate {expected_lastmod}"
            )

    return errors


def main(argv: list[str]) -> int:
    public_dir = Path(argv[1]) if len(argv) > 1 else Path("public")
    posts_dir = Path(argv[2]) if len(argv) > 2 else Path("content/posts")
    errors = audit_feed_and_sitemap(public_dir, posts_dir)
    if not errors:
        print("    ok")
        return 0
    for error in errors[:40]:
        print(f"    {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
