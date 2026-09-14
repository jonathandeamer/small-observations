#!/usr/bin/env python3
"""Check structural accessibility and head invariants on every rendered page.

Minified HTML omits optional end tags such as </p>, so this parser never keeps
an element stack; it only tracks tags whose end tags are required.
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

FEED_URL = "https://smallobservations.net/feed.xml"
BROWSE_LINKS = ("/posts/", "/tags/", "/cities/", "/years/", "/countries/", "/artists/")
HEAD_LINKS = ("/favicon.svg", "/favicon.ico", "/apple-touch-icon.png")


def _classes(attr: dict[str, str]) -> set[str]:
    return set(attr.get("class", "").split())


class _StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.is_alias = False
        self.h1_classes: list[set[str]] = []
        self.p_masthead_title = False
        self.after_body = False
        self.first_body_element: tuple[str, dict[str, str]] | None = None
        self.main_content_tag = ""
        self.in_browse_nav = False
        self.browse_nav_label: str | None = None
        self.browse_hrefs: list[str] = []
        self.canonical = ""
        self.rss = ""
        self.head_hrefs: set[str] = set()
        self.preloads: list[str] = []
        self.first_img: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {name: value or "" for name, value in attrs}
        classes = _classes(attr)
        if tag == "meta" and attr.get("http-equiv", "").lower() == "refresh":
            self.is_alias = True
        if tag == "body":
            self.after_body = True
            return
        if self.after_body and self.first_body_element is None:
            self.first_body_element = (tag, attr)
        if attr.get("id") == "main-content":
            self.main_content_tag = tag
        if tag == "h1":
            self.h1_classes.append(classes)
        if tag == "p" and "masthead-title" in classes:
            self.p_masthead_title = True
        if tag == "nav" and "masthead-browse" in classes:
            self.in_browse_nav = True
            self.browse_nav_label = attr.get("aria-label", "").strip()
        if tag == "a" and self.in_browse_nav:
            self.browse_hrefs.append(attr.get("href", ""))
        if tag == "img" and self.first_img is None:
            self.first_img = attr
        if tag == "link":
            rels = set(attr.get("rel", "").lower().split())
            href = attr.get("href", "")
            if "canonical" in rels:
                self.canonical = href
            if "alternate" in rels and attr.get("type") == "application/rss+xml":
                self.rss = href
            if rels & {"icon", "apple-touch-icon"}:
                self.head_hrefs.add(href)
            if "preload" in rels:
                self.preloads.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "nav":
            self.in_browse_nav = False


def audit_page(text: str, label: str, public_dir: Path, is_home: bool) -> list[str]:
    p = _StructureParser()
    p.feed(text)
    p.close()
    if p.is_alias:
        return []
    errors: list[str] = []

    if len(p.h1_classes) != 1:
        errors.append(f"{label}: expected 1 <h1>, found {len(p.h1_classes)}")
    elif is_home and "masthead-title" not in p.h1_classes[0]:
        errors.append(f"{label}: home <h1> must be the site title (class masthead-title)")
    if not is_home:
        if not p.p_masthead_title:
            errors.append(f"{label}: site title must be <p class=masthead-title> on non-home pages")
        if any("masthead-title" in classes for classes in p.h1_classes):
            errors.append(f"{label}: <h1> must describe the page, not be the site title")

    first = p.first_body_element
    if not (
        first
        and first[0] == "a"
        and "skip-nav" in _classes(first[1])
        and first[1].get("href") == "#main-content"
    ):
        errors.append(f"{label}: first element in <body> must be <a class=skip-nav href=#main-content>")
    if p.main_content_tag != "main":
        errors.append(f"{label}: #main-content must be a <main> element")

    if p.browse_nav_label is None:
        errors.append(f"{label}: missing <nav class=masthead-browse>")
    else:
        if not p.browse_nav_label:
            errors.append(f"{label}: <nav class=masthead-browse> needs an aria-label")
        missing = [href for href in BROWSE_LINKS if href not in p.browse_hrefs]
        if missing:
            errors.append(f"{label}: browse nav missing links to {', '.join(missing)}")

    if not p.canonical:
        errors.append(f"{label}: missing canonical link")
    if p.rss != FEED_URL:
        errors.append(f"{label}: RSS autodiscovery must point at {FEED_URL}")
    for href in HEAD_LINKS:
        if href not in p.head_hrefs:
            errors.append(f"{label}: missing head link {href}")
    for href in p.preloads:
        if not (public_dir / href.lstrip("/")).is_file():
            errors.append(f"{label}: preload {href} does not exist in public/")

    if is_home and not (
        p.first_img
        and p.first_img.get("loading") == "eager"
        and p.first_img.get("fetchpriority") == "high"
    ):
        errors.append(f"{label}: first <img> must have loading=eager and fetchpriority=high")

    return errors


def audit_site(public_dir: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(public_dir.rglob("*.html")):
        rel = path.relative_to(public_dir).as_posix()
        errors.extend(audit_page(path.read_text(), rel, public_dir, is_home=rel == "index.html"))
    return errors


def main(argv: list[str]) -> int:
    public_dir = Path(argv[1]) if len(argv) > 1 else Path("public")
    errors = audit_site(public_dir)
    if not errors:
        print("    ok")
        return 0
    for error in errors[:40]:
        print(f"    {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
