#!/usr/bin/env python3
"""Check every post page still exposes an h-entry microformat.

Properties only count if they appear after the h-entry element opens. There is
no element stack because minified HTML omits optional end tags.
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path


class _MicroformatParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.is_alias = False
        self.entries = 0
        self.name_text: list[str] = []
        self._name_tag = ""
        self.photo = False
        self.published = False
        self.author = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {name: value or "" for name, value in attrs}
        classes = set(attr.get("class", "").split())
        if tag == "meta" and attr.get("http-equiv", "").lower() == "refresh":
            self.is_alias = True
        if "h-entry" in classes:
            self.entries += 1
            return
        if not self.entries:
            return
        if "p-name" in classes and not self.name_text:
            self._name_tag = tag
        if tag == "img" and "u-photo" in classes and attr.get("src"):
            self.photo = True
        if "dt-published" in classes and attr.get("datetime"):
            self.published = True
        if {"p-author", "h-card"} <= classes and attr.get("href"):
            self.author = True

    def handle_endtag(self, tag: str) -> None:
        if tag == self._name_tag:
            self._name_tag = ""

    def handle_data(self, data: str) -> None:
        if self._name_tag and data.strip():
            self.name_text.append(data.strip())


def audit_post(text: str, label: str) -> list[str]:
    p = _MicroformatParser()
    p.feed(text)
    p.close()
    if p.is_alias:
        return []
    errors: list[str] = []
    if p.entries != 1:
        errors.append(f"{label}: expected 1 h-entry, found {p.entries}")
        if p.entries == 0:
            return errors
    if not p.name_text:
        errors.append(f"{label}: missing non-empty p-name")
    if not p.photo:
        errors.append(f"{label}: missing <img class=u-photo src=...>")
    if not p.published:
        errors.append(f"{label}: missing dt-published with datetime attribute")
    if not p.author:
        errors.append(f"{label}: missing p-author h-card with href")
    return errors


def audit_posts(public_dir: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(public_dir.glob("[0-9]*/*/*/index.html")):
        errors.extend(audit_post(path.read_text(), path.relative_to(public_dir).as_posix()))
    return errors


def main(argv: list[str]) -> int:
    public_dir = Path(argv[1]) if len(argv) > 1 else Path("public")
    errors = audit_posts(public_dir)
    if not errors:
        print("    ok")
        return 0
    for error in errors[:40]:
        print(f"    {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
