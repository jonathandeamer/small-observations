#!/usr/bin/env python3
"""Check the build stays JS-free, loads nothing off-site, fits its budgets,
and deploys every file with an explicit Cache-Control matcher."""

from __future__ import annotations

import re
import sys
import tomllib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

SITE_HOST = "smallobservations.net"
# 8,567 bytes on 2026-09-14; room for a redesign, not for a framework.
MAX_INLINE_CSS_BYTES = 16_000
# 134,244 bytes on 2026-09-14 — already a deliberate overage of the 80 KB spec budget.
MAX_FONT_BYTES = 140_000
# Files that deliberately deploy with S3's default metadata.
UNMATCHED_OK = frozenset({"favicon.ico", "robots.txt"})

NAVIGATIONAL_RELS = frozenset({"canonical", "alternate", "me", "author"})
EMBEDDING_TAGS = frozenset({"iframe", "embed", "object", "frame"})
RESOURCE_ATTRS = ("src", "poster", "data")
CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^'\")\s]+)")
CSS_IMPORT_RE = re.compile(r"@import", re.IGNORECASE)


def is_local(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme == "data":
        return True
    if not parsed.netloc:
        return not parsed.scheme
    return parsed.hostname == SITE_HOST


class _ResourceParser(HTMLParser):
    def __init__(self, label: str) -> None:
        super().__init__(convert_charrefs=True)
        self.label = label
        self.errors: list[str] = []
        self.css_bytes = 0
        self._in_style = False

    def _css(self, css: str) -> None:
        if CSS_IMPORT_RE.search(css):
            self.errors.append(f"{self.label}: CSS @import not allowed")
        for url in CSS_URL_RE.findall(css):
            if not is_local(url):
                self.errors.append(f"{self.label}: CSS url() loads off-site {url}")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {name: value or "" for name, value in attrs}
        if tag in EMBEDDING_TAGS:
            self.errors.append(f"{self.label}: <{tag}> not allowed")
            return
        if tag == "style":
            self._in_style = True
        if "style" in attr:
            self._css(attr["style"])
        if tag == "script":
            if "src" in attr:
                self.errors.append(f"{self.label}: <script> with src={attr['src']}")
            elif attr.get("type") != "application/ld+json":
                self.errors.append(f"{self.label}: <script> without type=application/ld+json")
            return
        if tag == "link":
            rels = attr.get("rel", "").lower().split()
            href = attr.get("href", "")
            if rels and set(rels) <= NAVIGATIONAL_RELS:
                return
            if href and not is_local(href):
                self.errors.append(f"{self.label}: <link rel={' '.join(rels)}> loads off-site {href}")
            return
        for name in RESOURCE_ATTRS:
            if attr.get(name) and not is_local(attr[name]):
                self.errors.append(f"{self.label}: <{tag} {name}> loads off-site {attr[name]}")
        for candidate in attr.get("srcset", "").split(","):
            url = candidate.strip().split(" ")[0]
            if url and not is_local(url):
                self.errors.append(f"{self.label}: <{tag} srcset> loads off-site {url}")

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self.css_bytes += len(data.encode())
            self._css(data)


def audit_html(text: str, label: str, max_css_bytes: int = MAX_INLINE_CSS_BYTES) -> list[str]:
    parser = _ResourceParser(label)
    parser.feed(text)
    parser.close()
    errors = parser.errors
    if parser.css_bytes > max_css_bytes:
        errors.append(f"{label}: inline CSS is {parser.css_bytes} bytes (budget {max_css_bytes})")
    return errors


def font_budget_errors(public_dir: Path, max_font_bytes: int = MAX_FONT_BYTES) -> list[str]:
    total = sum(p.stat().st_size for p in (public_dir / "fonts").rglob("*") if p.is_file())
    return [f"fonts/: {total} bytes (budget {max_font_bytes})"] if total > max_font_bytes else []


def deployed_by_hugo(rel_path: str) -> bool:
    # hugo deploy skips .DS_Store files and hidden directories except .well-known.
    *dirs, name = rel_path.split("/")
    if name == ".DS_Store":
        return False
    return not any(d.startswith(".") and d != ".well-known" for d in dirs)


def deploy_matcher_errors(public_dir: Path, hugo_toml: str) -> list[str]:
    config = tomllib.loads(hugo_toml)
    patterns = [re.compile(m["pattern"]) for m in config.get("deployment", {}).get("matchers", [])]
    errors: list[str] = []
    for path in sorted(p for p in public_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(public_dir).as_posix()
        if not deployed_by_hugo(rel):
            continue
        if rel in UNMATCHED_OK or any(p.search(rel) for p in patterns):
            continue
        errors.append(
            f"{rel}: matches no [[deployment.matchers]] pattern (would deploy without Cache-Control)"
        )
    return errors


def audit_public(public_dir: Path, hugo_toml: str) -> list[str]:
    errors: list[str] = []
    for path in sorted(public_dir.rglob("*.html")):
        errors.extend(audit_html(path.read_text(), path.relative_to(public_dir).as_posix()))
    errors.extend(font_budget_errors(public_dir))
    errors.extend(deploy_matcher_errors(public_dir, hugo_toml))
    return errors


def main(argv: list[str]) -> int:
    public_dir = Path(argv[1]) if len(argv) > 1 else Path("public")
    hugo_toml = Path(argv[2] if len(argv) > 2 else "hugo.toml").read_text()
    errors = audit_public(public_dir, hugo_toml)
    if not errors:
        print("    ok")
        return 0
    for error in errors[:40]:
        print(f"    {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
