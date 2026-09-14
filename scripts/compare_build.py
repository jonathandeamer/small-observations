#!/usr/bin/env python3
"""Compare two Hugo builds and fail on anything that isn't visual design.

HTML is normalised before comparison: inline <style> contents and design-only
class names are dropped, attributes sorted, whitespace collapsed. Every other
file must be byte-identical, except the design assets in DESIGN_PATHS, which
are reported but allowed to change.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

# Classes something other than site.css depends on: microformats consumers,
# pa11y.json hideElements, and the page-structure audits. Every other class
# is design vocabulary a redesign may rename freely.
MICROFORMAT_CLASS_RE = re.compile(r"^(?:h|p|u|dt|e)-[a-z]")
CONTRACT_CLASSES = frozenset(
    {"sr-only", "skip-nav", "glyph", "terms-sort-sep", "masthead-title", "masthead-browse"}
)

# Output a redesign may legitimately change. Reported, never a failure.
DESIGN_PATHS = ("fonts/", "favicon.svg", "favicon.ico", "apple-touch-icon.png")


def _keep_class(name: str) -> bool:
    return name in CONTRACT_CLASSES or bool(MICROFORMAT_CLASS_RE.match(name))


def _format_attrs(attrs: list[tuple[str, str | None]]) -> str:
    parts: list[str] = []
    for name, value in sorted(attrs, key=lambda item: item[0]):
        if name == "class":
            kept = sorted(c for c in (value or "").split() if _keep_class(c))
            if not kept:
                continue
            value = " ".join(kept)
        parts.append(name if value is None else f'{name}="{value}"')
    return "".join(f" {part}" for part in parts)


class _Normaliser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self._in_style = False

    def handle_decl(self, decl: str) -> None:
        self.lines.append(f"<!{decl.lower()}>")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "style":
            self._in_style = True
        self.lines.append(f"<{tag}{_format_attrs(attrs)}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.lines.append(f"<{tag}{_format_attrs(attrs)}>")

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self._in_style = False
        self.lines.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._in_style:
            return
        text = " ".join(data.split())
        if text:
            self.lines.append(text)

    def handle_comment(self, data: str) -> None:
        self.lines.append(f"<!-- {' '.join(data.split())} -->")


def normalise_html(text: str) -> str:
    parser = _Normaliser()
    parser.feed(text)
    parser.close()
    return "\n".join(parser.lines) + "\n"


def is_design_path(rel_path: str) -> bool:
    return any(
        rel_path.startswith(prefix) if prefix.endswith("/") else rel_path == prefix
        for prefix in DESIGN_PATHS
    )


@dataclass
class BuildDiff:
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    design_changes: list[str] = field(default_factory=list)
    html_diffs: dict[str, str] = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def _files(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def compare_trees(base: Path, head: Path) -> BuildDiff:
    diff = BuildDiff()
    base_files, head_files = _files(base), _files(head)
    for rel in sorted(base_files | head_files):
        in_base, in_head = rel in base_files, rel in head_files
        if in_base and in_head:
            if rel.endswith(".html"):
                old = normalise_html((base / rel).read_text())
                new = normalise_html((head / rel).read_text())
                differs = old != new
            else:
                differs = (base / rel).read_bytes() != (head / rel).read_bytes()
            if not differs:
                continue
            if is_design_path(rel):
                diff.design_changes.append(rel)
                continue
            diff.changed.append(rel)
            if rel.endswith(".html"):
                diff.html_diffs[rel] = "".join(
                    difflib.unified_diff(
                        old.splitlines(keepends=True),
                        new.splitlines(keepends=True),
                        fromfile=f"base/{rel}",
                        tofile=f"head/{rel}",
                        n=2,
                    )
                )
        elif is_design_path(rel):
            diff.design_changes.append(rel)
        elif in_head:
            diff.added.append(rel)
        else:
            diff.removed.append(rel)
    return diff


def format_report(diff: BuildDiff, max_html_diffs: int = 5, max_diff_lines: int = 60) -> str:
    out: list[str] = []
    for label, paths in (("added", diff.added), ("removed", diff.removed), ("changed", diff.changed)):
        if paths:
            out.append(f"    {label} ({len(paths)}):")
            out.extend(f"      {p}" for p in paths[:40])
            if len(paths) > 40:
                out.append(f"      … and {len(paths) - 40} more")
    for rel, text in list(diff.html_diffs.items())[:max_html_diffs]:
        lines = text.splitlines()
        out.append("")
        out.extend(f"    {line}" for line in lines[:max_diff_lines])
        if len(lines) > max_diff_lines:
            out.append(f"    … diff truncated ({len(lines) - max_diff_lines} more lines)")
    if len(diff.html_diffs) > max_html_diffs:
        out.append(f"    … {len(diff.html_diffs) - max_html_diffs} more HTML files differ")
    if diff.design_changes:
        out.append(f"    design assets changed (allowed, {len(diff.design_changes)}):")
        out.extend(f"      {p}" for p in diff.design_changes)
    return "\n".join(out)
