# Redesign Safety Net Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add automated checks so a visual redesign (colour scheme, typography) can't silently change layout structure, functionality, RSS/sitemap/llms.txt output, CDN caching behaviour, or ingest.

**Architecture:** Two kinds of check. (1) A *baseline comparison* (`make compare`) builds the current content twice — once with the theme from a base git ref, once with the working-tree theme — and fails on any output difference other than inline CSS, design-only class names, and font/favicon files. (2) *Invariant audits* (`make audit`, run by `make check`) that assert properties of the build that must hold regardless of baseline: no JS/third-party requests, size budgets, page structure, microformats, pa11y on every page type. `make check` is also fixed so failing audits actually fail.

**Tech Stack:** GNU make, Python 3 stdlib (`html.parser`, `tomllib`, `difflib`, `subprocess`), pytest, Hugo 0.161 extended, pa11y, htmltest, vnu, xmllint.

**Spec:** No separate spec doc. Design decisions were agreed in conversation on 2026-09-14 and are recorded in "Design decisions" below.

## Global Constraints

- The published site stays JS-free with no third-party requests. Nothing in this plan changes templates, CSS, content, `hugo.toml`, ingest, or deploy targets, apart from `pa11y.json` and the Makefile `check` target.
- Never run plain `hugo` into `public/`. The comparison builds go to `tmp/compare/` (already gitignored via `/tmp/`) using `-d`.
- Commit messages must match `type(scope): subject`. Use `build(config)` for check scripts and Makefile audit changes, `docs(config)` for CLAUDE.md-only changes. Subject lowercase, no trailing period, ≤72 chars. Never `--no-verify`.
- End every commit message with:
  ```
  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01T8wJxhYYmrDNg3xDk819ma
  ```
- New check scripts follow the existing pattern in `scripts/check_rendered_metadata.py`: stdlib only, a pure `audit_*` function returning `list[str]` of errors, `main(argv)` printing `    ok` or the first 40 errors and returning 0/1. Tests live in `tests/test_<script>.py` and import `from scripts.<module> import ...`.
- Built HTML is minified: attribute quotes are stripped (`class=foo`) and optional end tags such as `</p>` may be omitted. Parsers must not rely on a `<p>`/`<li>` element stack. Tags with required end tags (`</nav>`, `</h1>`, `</main>`, `</head>`, `</body>`) are present.
- Hugo alias redirect pages (3 today) contain `<meta http-equiv=refresh ...>`, have no `<body>`, and are skipped by every per-page audit.
- `make` on this machine is Apple's GNU Make 3.81. It ignores `.SHELLFLAGS` and has no `--eval`. Recipes run under `/bin/sh -c` without `-e`, so every multi-command recipe line whose failure matters must start with `set -e;`, and no command whose exit status matters may be piped into another.
- Run tests with `make test`. Run `pa11y` and `make check`/`make audit` with normal local permissions (pa11y can't launch Chromium in a sandbox).

## Design decisions

Facts established on 2026-09-14 against commit `00cf5da`:

- Two consecutive `hugo --minify` builds are byte-identical, and a build with `--themesDir` pointing at a `git archive` of `themes/` from HEAD is byte-identical to a normal build. The baseline comparison relies on both. Each build takes under 1s with a warm `resources/_gen/`.
- The comparison builds **current content with the base theme**, not a checkout of the base ref. Posts added to `main` during the redesign therefore don't show up as differences. `hugo.toml`, Makefile deploy/ingest recipes and `ingest/` are compared against the base ref separately.
- Normalisation removes `<style>` element contents and every class token *except* those something other than `site.css` depends on: microformats (`h-*`, `p-*`, `u-*`, `dt-*`, `e-*`) and the contract classes `sr-only`, `skip-nav`, `glyph`, `terms-sort-sep`, `masthead-title`, `masthead-browse`. It also sorts attributes and collapses whitespace. `style="…"` attributes are kept: the one in use (`display: none` on the `p-author h-card`) is functional.
- Output a redesign may legitimately change is reported but never fails: `fonts/`, `favicon.svg`, `favicon.ico`, `apple-touch-icon.png`. Everything else — `feed.xml`, `sitemap.xml`, `llms.txt`, `robots.txt`, every image derivative — must be byte-identical.
- Before this plan, every audit passes but `make check` ignores failures from pa11y (home page), vnu (`|| true`), xmllint (`|| echo`) and htmltest (`| tail`).
- pa11y passes on home, a post, `/posts/`, `/cities/`, `/years/` and `/404.html`. It fails on `/tags/`, `/tags/by-count/`, `/tags/favourite/` and `/years/2018/`, all with the same single issue: the decorative `<span class="terms-sort-sep" aria-hidden="true">·</span>` in `--coral` (3.74:1). That's the same case as the already-suppressed `.glyph`, so it is added to `hideElements`.
- Make 3.81 was verified to fail a recipe when `set -e;` starts an `if … for … done … fi` block and a command inside the loop fails. `make -n audit` prints recipes with `$(SAMPLE_POST)` expanded, which the verification steps use instead of `--eval`.
- Only `favicon.ico` and `robots.txt` in `public/` match no `[[deployment.matchers]]` pattern today.
- Budgets: inline CSS is 8,567 bytes, so the limit is set at 16,000. `public/fonts/` is 134,244 bytes (already a deliberate overage of the 80 KB spec budget), so the limit is set at 140,000.
- Layout-geometry testing with Playwright is out of scope for this plan and deferred to a follow-up.

## File structure

| File | Responsibility |
|---|---|
| `Makefile` (modify) | `SHELL`/`.SHELLFLAGS` so pipelines fail; split `check` into `build` + new `audit`; `PA11Y_PAGES`; new `compare` target |
| `pa11y.json` (modify) | add `.terms-sort-sep` to `hideElements` |
| `scripts/compare_build.py` (create) | HTML normalisation, tree comparison, config/Makefile/ingest guards, orchestration of the two builds |
| `tests/test_compare_build.py` (create) | unit tests for the pure parts of `compare_build.py` |
| `scripts/check_no_third_party.py` (create) | no JS, no off-site resource loads, CSS and font byte budgets, every file covered by a deploy matcher |
| `tests/test_check_no_third_party.py` (create) | tests |
| `scripts/check_page_structure.py` (create) | one `<h1>`, skip link, `<main id>`, browse nav, head links, preload targets exist, home LCP image |
| `tests/test_check_page_structure.py` (create) | tests |
| `scripts/check_microformats.py` (create) | h-entry properties on every post page |
| `tests/test_check_microformats.py` (create) | tests |
| `CLAUDE.md` (modify) | document `make audit`, `make compare`, the new checks and the redesign workflow |

---

### Task 1: Make audit failures fail the build

**Files:**
- Modify: `Makefile` (top of file; `.PHONY`; the whole `check:` target)
- Modify: `CLAUDE.md` (Commands block)

**Interfaces:**
- Produces: `make audit` (runs every audit against the existing `public/`, no rebuild); `make check` = `make build` then `make audit`; Make variable `SAMPLE_POST` (path of the first non-alias post page). Tasks 2, 5, 6 and 7 add lines to the `audit:` recipe.

- [ ] **Step 1: Prove the current gap exists**

Run: `make build && sed -i '' 's/"hideElements"/"hideElementsDisabled"/' pa11y.json && make check; echo "exit=$?"; git checkout pa11y.json`

Expected: pa11y prints contrast errors for `.glyph` on the homepage, yet the output ends with `exit=0`. That is the bug.

- [ ] **Step 2: Add the sample-post variable**

In `Makefile`, directly after `.DEFAULT_GOAL := help`, add:

```make
# First real post page (alias redirect pages contain http-equiv and are skipped).
# Recursive (=) so it's evaluated after build has produced public/.
SAMPLE_POST = $(firstword $(shell grep -L 'http-equiv' public/[0-9]*/*/*/index.html 2>/dev/null))
```

Change the `.PHONY` line to:

```make
.PHONY: help dev build check audit clean deploy deploy-dry ingest ingest-dry test venv stats
```

- [ ] **Step 3: Replace the `check:` target with `check:` + `audit:`**

Replace the entire existing `check: build  ## build then sanity-check the rendered site` target (through the final `@echo` after the RSS feed validity block) with:

```make
check: build  ## build then run every audit; fails on the first failing audit
	@$(MAKE) --no-print-directory audit

audit:  ## run every audit against the existing public/ (no rebuild)
	@test -f public/index.html || { echo "public/ is empty — run make build first"; exit 1; }
	@echo "→ photo post front matter:"
	@python3 scripts/check_post_frontmatter.py content/posts
	@echo
	@echo "→ photo post slugs:"
	@python3 scripts/audit_slugs.py
	@echo "    ok"
	@echo
	@echo "→ posts with empty alt text on their photo:"
	@python3 scripts/check_photo_alt.py public
	@echo
	@echo "→ rendered post metadata:"
	@python3 scripts/check_rendered_metadata.py public
	@echo
	@echo "→ RSS, sitemap, and llms.txt URL contracts:"
	@python3 scripts/check_feed_sitemap.py public content/posts
	@echo
	@if command -v htmltest >/dev/null 2>&1; then \
		set -e; \
		echo "→ htmltest (internal link check):"; \
		htmltest -s public; \
	else \
		echo "→ htmltest not installed (skipping link check)"; \
		echo "    install with: brew install htmltest"; \
	fi
	@echo
	@if command -v pa11y >/dev/null 2>&1; then \
		set -e; \
		for page in public/index.html $(SAMPLE_POST); do \
			echo "→ pa11y $$page"; \
			pa11y --config pa11y.json "file://$(CURDIR)/$$page"; \
		done; \
	else \
		echo "→ pa11y not installed (skipping accessibility check)"; \
		echo "    install with: npm install -g pa11y"; \
	fi
	@echo
	@if java -jar ~/.vnu/vnu.jar --version >/dev/null 2>&1; then \
		set -e; \
		echo "→ vnu HTML validation (homepage + one post):"; \
		java -jar ~/.vnu/vnu.jar --skip-non-html public/index.html $(SAMPLE_POST); \
		echo "    ok"; \
	else \
		echo "→ vnu HTML validator not installed (skipping)"; \
		echo "    install: mkdir -p ~/.vnu && curl -sL https://github.com/validator/validator/releases/latest/download/vnu.jar -o ~/.vnu/vnu.jar"; \
	fi
	@echo
	@echo "→ sitemap:"
	@test -s public/sitemap.xml && xmllint --noout public/sitemap.xml
	@echo "    ok ($$(grep -o '<loc>' public/sitemap.xml | wc -l | tr -d ' ') URLs)"
	@echo
	@echo "→ RSS feed validity:"
	@xmllint --noout public/feed.xml
	@echo "    ok"
	@echo
```

(Recipe lines must start with a real tab character, as in the rest of the Makefile. The `set -e;` lines are load-bearing: without them the shell's exit status is only that of the *last* command in the block, e.g. the final `echo "    ok"`.)

- [ ] **Step 4: Confirm the sample post resolves to a real post**

Run: `make build && make -n audit | grep 'vnu.jar --skip-non-html'`

Expected: the printed command ends with one path like `public/2005/09/seville-kurt-cobain/index.html`, not empty and not an alias page.

- [ ] **Step 5: Run the full check on a clean tree**

Run: `make check; echo "exit=$?"`

Expected: every section prints `ok`/`No issues found!`/`passed`, ending with `exit=0`.

- [ ] **Step 6: Prove pa11y failures now fail**

Run: `sed -i '' 's/"hideElements"/"hideElementsDisabled"/' pa11y.json; make audit; echo "exit=$?"; git checkout pa11y.json`

Expected: pa11y contrast errors followed by `make: *** [audit] Error 2` and `exit=2`.

- [ ] **Step 7: Prove vnu failures now fail**

Run: `sed -i '' 's/<main class=page/<main bogus-attr=1 class=page/' public/index.html; make audit; echo "exit=$?"; make build`

Expected: vnu reports `Attribute "bogus-attr" not allowed`, followed by a make error and a non-zero exit. The final `make build` restores `public/`.

- [ ] **Step 8: Prove xmllint failures now fail**

Run: `printf '<unclosed' >> public/sitemap.xml; make audit; echo "exit=$?"; make build`

Expected: non-zero exit. It doesn't matter whether `check_feed_sitemap.py` or xmllint reports it first.

- [ ] **Step 9: Document the targets**

In `CLAUDE.md`, in the Commands code block, replace the `make check` line with these two lines:

```
make check        # build, then `make audit`; any failing audit fails the target
make audit        # run every audit against the existing public/ without rebuilding
```

In the "Accessibility & web standards" section, change `**Automated checks** — all run by \`make check\`:` to `**Automated checks** — all run by \`make check\` / \`make audit\`, and any failure fails the target:`.

- [ ] **Step 10: Commit**

```bash
git add Makefile CLAUDE.md
git commit -m "build(config): make audit failures fail make check

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01T8wJxhYYmrDNg3xDk819ma"
```

---

### Task 2: Run pa11y on every page type

**Files:**
- Modify: `pa11y.json`
- Modify: `Makefile` (add `PA11Y_PAGES`; pa11y loop in `audit:`)
- Modify: `CLAUDE.md` (pa11y bullet)

**Interfaces:**
- Consumes: `SAMPLE_POST`, `audit:` from Task 1.
- Produces: Make variable `PA11Y_PAGES`.

- [ ] **Step 1: Confirm the known failures**

Run: `make build && pa11y --config pa11y.json "file://$PWD/public/tags/index.html"; echo "exit=$?"`

Expected: one contrast error on `<span class="terms-sort-sep" aria-hidden="true">·</span>`, `exit=2`.

- [ ] **Step 2: Hide the decorative separator from the contrast audit**

Replace the contents of `pa11y.json` with:

```json
{
  "hideElements": ".glyph, .terms-sort-sep"
}
```

- [ ] **Step 3: Add the page list**

In `Makefile`, directly after the `SAMPLE_POST = ...` line, add:

```make
# One page per template family. Extend when a new template is added.
PA11Y_PAGES = public/index.html $(SAMPLE_POST) public/posts/index.html \
	public/posts/page/2/index.html public/tags/index.html public/tags/by-count/index.html \
	public/tags/favourite/index.html public/cities/index.html public/countries/index.html \
	public/artists/index.html public/years/index.html public/years/2018/index.html \
	public/404.html
```

In the `audit:` recipe, change `for page in public/index.html $(SAMPLE_POST); do \` to `for page in $(PA11Y_PAGES); do \`.

- [ ] **Step 4: Confirm every listed page exists**

Run: `make -n audit | grep 'for page in'`, then `ls` every path printed after `for page in` (up to `; do`).

Expected: 13 paths, all present, no "No such file" errors. If one is missing (e.g. `posts/page/2/`), remove it from the list and mention that in the commit body.

- [ ] **Step 5: Run the audit**

Run: `make audit; echo "exit=$?"`

Expected: `No issues found!` for all 13 pages, then `exit=0`. If a page fails for anything other than an `aria-hidden` decorative element, **stop and report the issue** instead of adding it to `hideElements`.

- [ ] **Step 6: Document**

In `CLAUDE.md`, replace the pa11y bullet under "Automated checks" with:

```
- `pa11y` audits one page per template family (WCAG 2.1 AA): home, a post, `/posts/` and its page 2, the tags index and its by-count variant, a tag term, the cities/countries/artists/years indexes, a year term, and the 404. The list is `PA11Y_PAGES` in the Makefile — extend it when adding a template. Suppressions live in `pa11y.json`: decorative `aria-hidden="true"` flourishes in coral (`.glyph` in section headings, `.terms-sort-sep` between sort links) are hidden from the contrast audit because they are non-text decoration and coral on cream is intentionally below body-text contrast.
```

- [ ] **Step 7: Commit**

```bash
git add pa11y.json Makefile CLAUDE.md
git commit -m "build(config): run pa11y on every page type

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01T8wJxhYYmrDNg3xDk819ma"
```

---

### Task 3: Build comparison core (normalise + compare trees)

**Files:**
- Create: `scripts/compare_build.py`
- Test: `tests/test_compare_build.py`

**Interfaces:**
- Produces (used by Task 4):
  - `normalise_html(text: str) -> str`
  - `is_design_path(rel_path: str) -> bool`
  - `@dataclass BuildDiff` with fields `added: list[str]`, `removed: list[str]`, `changed: list[str]`, `design_changes: list[str]`, `html_diffs: dict[str, str]`, and property `failed -> bool`
  - `compare_trees(base: Path, head: Path) -> BuildDiff`
  - `format_report(diff: BuildDiff, max_html_diffs: int = 5, max_diff_lines: int = 60) -> str`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_compare_build.py`:

```python
from pathlib import Path

from scripts.compare_build import compare_trees, format_report, normalise_html


def page(head: str = "", body: str = "") -> str:
    return f"<!doctype html><html lang=en-gb><head>{head}</head><body>{body}</body></html>"


def write(root: Path, rel: str, content: str | bytes) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content)


def test_normalise_ignores_inline_css() -> None:
    a = page(head="<style>body{color:red}</style>")
    b = page(head="<style>body{color:blue;font-family:serif}</style>")
    assert normalise_html(a) == normalise_html(b)


def test_normalise_ignores_design_classes_attribute_order_and_whitespace() -> None:
    a = page(body='<div class="gallery-card old-name" id=x>  Hello\n  world </div>')
    b = page(body="<div id=x class=new-card>Hello world</div>")
    assert normalise_html(a) == normalise_html(b)


def test_normalise_keeps_microformat_classes() -> None:
    a = page(body='<article class="post h-entry">x</article>')
    b = page(body='<article class="post">x</article>')
    assert normalise_html(a) != normalise_html(b)


def test_normalise_keeps_contract_classes() -> None:
    a = page(body='<a class=skip-nav href="#main-content">Skip</a>')
    b = page(body='<a class=jump href="#main-content">Skip</a>')
    assert normalise_html(a) != normalise_html(b)


def test_normalise_keeps_text_links_and_style_attributes() -> None:
    base = page(body='<a href=/tags/ style="display: none;">tags</a>')
    assert normalise_html(base) != normalise_html(page(body='<a href=/tag/ style="display: none;">tags</a>'))
    assert normalise_html(base) != normalise_html(page(body='<a href=/tags/ style="display: none;">Tags</a>'))
    assert normalise_html(base) != normalise_html(page(body="<a href=/tags/>tags</a>"))


def test_normalise_keeps_head_metadata_and_jsonld() -> None:
    a = page(head='<link rel=canonical href=https://smallobservations.net/><script type=application/ld+json>{"a":1}</script>')
    b = page(head='<link rel=canonical href=https://smallobservations.net/><script type=application/ld+json>{"a":2}</script>')
    assert normalise_html(a) != normalise_html(b)


def test_identical_trees_pass(tmp_path: Path) -> None:
    for side in ("base", "head"):
        write(tmp_path / side, "index.html", page(body="<h1>Hi</h1>"))
        write(tmp_path / side, "feed.xml", "<rss/>")
    diff = compare_trees(tmp_path / "base", tmp_path / "head")
    assert not diff.failed


def test_css_and_design_class_only_change_passes(tmp_path: Path) -> None:
    write(tmp_path / "base", "index.html", page(head="<style>a{}</style>", body="<p class=tagline>x"))
    write(tmp_path / "head", "index.html", page(head="<style>b{}</style>", body="<p class=strapline>x"))
    assert not compare_trees(tmp_path / "base", tmp_path / "head").failed


def test_added_and_removed_files_fail(tmp_path: Path) -> None:
    write(tmp_path / "base", "img/a_hu_1.webp", b"a")
    write(tmp_path / "head", "img/a_hu_2.webp", b"a")
    diff = compare_trees(tmp_path / "base", tmp_path / "head")
    assert diff.failed
    assert diff.added == ["img/a_hu_2.webp"]
    assert diff.removed == ["img/a_hu_1.webp"]


def test_non_html_byte_change_fails(tmp_path: Path) -> None:
    write(tmp_path / "base", "feed.xml", "<rss>a</rss>")
    write(tmp_path / "head", "feed.xml", "<rss>b</rss>")
    diff = compare_trees(tmp_path / "base", tmp_path / "head")
    assert diff.changed == ["feed.xml"]
    assert diff.failed


def test_design_paths_are_reported_not_failed(tmp_path: Path) -> None:
    write(tmp_path / "base", "fonts/fraunces-latin.woff2", b"old")
    write(tmp_path / "head", "fonts/newfont.woff2", b"new")
    write(tmp_path / "base", "favicon.svg", "<svg>a</svg>")
    write(tmp_path / "head", "favicon.svg", "<svg>b</svg>")
    diff = compare_trees(tmp_path / "base", tmp_path / "head")
    assert not diff.failed
    assert diff.design_changes == ["favicon.svg", "fonts/fraunces-latin.woff2", "fonts/newfont.woff2"]


def test_html_change_fails_with_readable_diff(tmp_path: Path) -> None:
    write(tmp_path / "base", "404.html", page(body="<h1>Page not found.</h1>"))
    write(tmp_path / "head", "404.html", page(body="<h2>Page not found.</h2>"))
    diff = compare_trees(tmp_path / "base", tmp_path / "head")
    assert diff.changed == ["404.html"]
    assert "-<h1>" in diff.html_diffs["404.html"]
    assert "+<h2>" in diff.html_diffs["404.html"]
    report = format_report(diff)
    assert "404.html" in report
    assert "+<h2>" in report
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `make test`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.compare_build'`.

- [ ] **Step 3: Write the implementation**

Create `scripts/compare_build.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `make test`
Expected: all tests pass, including the 12 new ones in `test_compare_build.py`.

- [ ] **Step 5: Commit**

```bash
git add scripts/compare_build.py tests/test_compare_build.py
git commit -m "build(config): add normalised build tree comparison

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01T8wJxhYYmrDNg3xDk819ma"
```

---

### Task 4: `make compare` — base-theme build, config and ingest guards

**Files:**
- Modify: `scripts/compare_build.py` (append functions and `main`)
- Modify: `tests/test_compare_build.py` (append tests)
- Modify: `Makefile` (`BASE`, `compare` target, `.PHONY`)
- Modify: `CLAUDE.md` (Commands block; new "Redesign safety net" section)

**Interfaces:**
- Consumes: `compare_trees`, `format_report`, `BuildDiff` from Task 3.
- Produces:
  - `config_errors(base_toml: str, head_toml: str) -> list[str]`
  - `make_recipe(makefile: str, target: str) -> str`
  - `makefile_errors(base_makefile: str, head_makefile: str) -> list[str]`
  - `main(argv: list[str]) -> int` with CLI `python3 scripts/compare_build.py [--base REF] [--workdir DIR]`
  - `make compare [BASE=ref]`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_compare_build.py`:

```python
from scripts.compare_build import config_errors, make_recipe, makefile_errors

TOML = """
baseURL = "https://smallobservations.net/"
theme = "notebook"

[outputs]
  home = ["HTML", "RSS", "LLMS"]

[[deployment.matchers]]
  pattern = "^feed\\\\.xml$"
  cacheControl = "public, max-age=0, must-revalidate"

[params]
  description = "A notebook of street art."
  measure = "34rem"
"""


def test_config_identical_passes() -> None:
    assert config_errors(TOML, TOML) == []


def test_config_design_param_may_change() -> None:
    assert config_errors(TOML, TOML.replace('"34rem"', '"38rem"')) == []


def test_config_deployment_change_fails() -> None:
    errors = config_errors(TOML, TOML.replace("max-age=0", "max-age=60"))
    assert errors == ["hugo.toml: [deployment] differs from base"]


def test_config_non_design_param_change_fails() -> None:
    errors = config_errors(TOML, TOML.replace("A notebook", "The notebook"))
    assert errors == ["hugo.toml: params.description differs from base"]


def test_config_top_level_scalar_change_fails() -> None:
    errors = config_errors(TOML, TOML.replace('theme = "notebook"', 'theme = "new"'))
    assert errors == ["hugo.toml: [theme] differs from base"]


MAKEFILE = """
build:  ## production build
\thugo --cleanDestinationDir --minify --gc --printPathWarnings

deploy: build  ## deploy
\tAWS_PROFILE=hugo-deploy hugo deploy --target production

deploy-dry: build  ## dry
\tAWS_PROFILE=hugo-deploy hugo deploy --target production --dryRun

ingest:  ## ingest
\t. .venv/bin/activate && python -m ingest
"""


def test_make_recipe_extracts_target_without_matching_prefixes() -> None:
    assert make_recipe(MAKEFILE, "deploy") == (
        "deploy: build\n\tAWS_PROFILE=hugo-deploy hugo deploy --target production"
    )


def test_makefile_help_text_change_passes() -> None:
    assert makefile_errors(MAKEFILE, MAKEFILE.replace("## deploy", "## ship it")) == []


def test_makefile_deploy_recipe_change_fails() -> None:
    errors = makefile_errors(MAKEFILE, MAKEFILE.replace("--target production\n\n", "--target staging\n\n"))
    assert errors == ["Makefile: `deploy` recipe differs from base"]


def test_makefile_missing_target_fails() -> None:
    errors = makefile_errors(MAKEFILE, MAKEFILE.replace("ingest:", "slurp:"))
    assert errors == ["Makefile: `ingest` recipe differs from base"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `make test`
Expected: FAIL with `ImportError: cannot import name 'config_errors' from 'scripts.compare_build'`.

- [ ] **Step 3: Write the implementation**

In `scripts/compare_build.py`, add these imports to the existing import block (keep it sorted):

```python
import argparse
import shutil
import subprocess
import sys
import tomllib
```

Append to the end of `scripts/compare_build.py`:

```python
# hugo.toml [params] keys a redesign may change. Everything else in hugo.toml
# (deployment matchers, outputs, permalinks, taxonomies, baseURL) is contract.
DESIGN_PARAMS = frozenset({"measure"})

# Makefile recipes a redesign must not touch.
PROTECTED_MAKE_TARGETS = ("build", "clean", "deploy", "deploy-dry", "ingest", "ingest-dry")

# Paths a redesign must not touch at all.
PROTECTED_PATHS = ("ingest", "pyproject.toml")


def config_errors(base_toml: str, head_toml: str) -> list[str]:
    base, head = tomllib.loads(base_toml), tomllib.loads(head_toml)
    errors: list[str] = []
    for key in sorted(set(base) | set(head)):
        if key == "params":
            base_params, head_params = base.get(key, {}), head.get(key, {})
            for param in sorted(set(base_params) | set(head_params)):
                if param in DESIGN_PARAMS:
                    continue
                if base_params.get(param) != head_params.get(param):
                    errors.append(f"hugo.toml: params.{param} differs from base")
        elif base.get(key) != head.get(key):
            errors.append(f"hugo.toml: [{key}] differs from base")
    return errors


def make_recipe(makefile: str, target: str) -> str:
    lines = makefile.splitlines()
    for index, line in enumerate(lines):
        if re.match(rf"^{re.escape(target)}:", line):
            recipe = [line.split("##")[0].rstrip()]
            for following in lines[index + 1 :]:
                if not following.startswith("\t"):
                    break
                recipe.append(following.rstrip())
            return "\n".join(recipe)
    return ""


def makefile_errors(base_makefile: str, head_makefile: str) -> list[str]:
    return [
        f"Makefile: `{target}` recipe differs from base"
        for target in PROTECTED_MAKE_TARGETS
        if make_recipe(base_makefile, target) != make_recipe(head_makefile, target)
    ]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def protected_path_errors(base_ref: str) -> list[str]:
    changed = _git("diff", "--name-only", base_ref, "--", *PROTECTED_PATHS).split()
    return [f"{path}: changed since {base_ref} (protected)" for path in changed]


def extract_theme(base_ref: str, dest: Path) -> Path:
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    archive = subprocess.run(["git", "archive", base_ref, "themes"], check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
    return dest / "themes"


def hugo_build(dest: Path, themes_dir: Path | None = None) -> None:
    cmd = ["hugo", "--minify", "--cleanDestinationDir", "--quiet", "-d", str(dest)]
    if themes_dir is not None:
        cmd += ["--themesDir", str(themes_dir)]
    subprocess.run(cmd, check=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="main", help="git ref whose theme is the baseline (default: main)")
    parser.add_argument("--workdir", default="tmp/compare", type=Path)
    args = parser.parse_args(argv[1:])

    errors = config_errors(_git("show", f"{args.base}:hugo.toml"), Path("hugo.toml").read_text())
    errors += makefile_errors(_git("show", f"{args.base}:Makefile"), Path("Makefile").read_text())
    errors += protected_path_errors(args.base)

    themes_dir = extract_theme(args.base, args.workdir / "base-src")
    hugo_build(args.workdir / "base", themes_dir)
    hugo_build(args.workdir / "head")
    diff = compare_trees(args.workdir / "base", args.workdir / "head")

    print(f"→ build output vs theme from {args.base} (same content):")
    for error in errors:
        print(f"    {error}")
    report = format_report(diff)
    if report:
        print(report)
    if errors or diff.failed:
        return 1
    print("    ok — only CSS, design classes, fonts and favicons differ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `make test`
Expected: all tests pass.

- [ ] **Step 5: Add the make target**

In `Makefile`, add `compare` to the `.PHONY` line. After the `audit:` target, add:

```make
BASE ?= main
compare:  ## compare build output against BASE's theme (default main); non-design changes fail
	python3 scripts/compare_build.py --base $(BASE)
```

- [ ] **Step 6: Verify a clean tree compares identical**

Run: `make compare BASE=HEAD; echo "exit=$?"`

Expected: `ok — only CSS, design classes, fonts and favicons differ`, `exit=0`. (Use `BASE=HEAD` here because this branch's own Makefile/scripts differ from `main` until merged. The Makefile guard only looks at protected recipes, so `BASE=main` should also pass. Run it and confirm.)

- [ ] **Step 7: Verify a CSS-only change passes**

Run: `sed -i '' 's/--bg:       #f4ede0;/--bg:       #ffffff;/' themes/notebook/assets/css/site.css; make compare BASE=HEAD; echo "exit=$?"; git checkout themes/notebook/assets/css/site.css`

Expected: `ok …`, `exit=0`.

- [ ] **Step 8: Verify a markup change fails with a readable diff**

Run: `sed -i '' 's/a notebook of street art I/A notebook of street art I/' themes/notebook/layouts/partials/masthead.html; make compare BASE=HEAD; echo "exit=$?"; git checkout themes/notebook/layouts/partials/masthead.html`

Expected: `changed (…)` listing many HTML files, a unified diff showing `-a notebook…` / `+A notebook…`, and a non-zero exit.

- [ ] **Step 9: Verify a deploy-config change fails**

Run: `sed -i '' 's/max-age=31536000, no-transform, public/max-age=60, public/' hugo.toml; make compare BASE=HEAD; echo "exit=$?"; git checkout hugo.toml`

Expected: `hugo.toml: [deployment] differs from base`, non-zero exit.

- [ ] **Step 10: Document**

In `CLAUDE.md` Commands block, after the `make audit` line, add:

```
make compare      # build with BASE's theme (default main) and the current theme over the same content; fail on non-design differences
```

Add a new section after "Accessibility & web standards":

```markdown
## Redesign safety net — `make compare`

For visual redesigns (colour, typography) that must not change structure, feeds, caching or ingest. `scripts/compare_build.py` builds the *current* content twice into `tmp/compare/` — once with `themes/` extracted from `BASE` via `git archive`, once with the working-tree theme — and compares them:

- **HTML** is normalised: `<style>` contents dropped, attributes sorted, whitespace collapsed, and class tokens dropped *except* microformats (`h-*`, `p-*`, `u-*`, `dt-*`, `e-*`) and the contract classes in `CONTRACT_CLASSES` (`sr-only`, `skip-nav`, `glyph`, `terms-sort-sep`, `masthead-title`, `masthead-browse`) that pa11y config and the audits depend on. Any other difference — text, links, headings, `<head>`, JSON-LD, `srcset`/`sizes`, `loading`/`fetchpriority`, `style=` attributes — fails.
- **Everything else** must be byte-identical: `feed.xml`, `sitemap.xml`, `llms.txt`, `robots.txt`, every image derivative. Only `fonts/` and the favicon trio may differ (reported, not failed).
- **Outside the build:** `hugo.toml` must match `BASE` except `params.measure`; the `build`, `clean`, `deploy`, `deploy-dry`, `ingest`, `ingest-dry` Makefile recipes must match; `ingest/` and `pyproject.toml` must be unchanged.

Workflow: on the redesign branch run `make compare` (vs `main`) for the cumulative picture, and `make compare BASE=HEAD` before each commit to see just that step. When a markup change is intentional (e.g. a wrapper element a new style needs), review the diff it prints and commit it — later `BASE=HEAD` comparisons start from there. If you add a class that pa11y config or an audit depends on, add it to `CONTRACT_CLASSES`; if a new `[params]` key is purely visual, add it to `DESIGN_PARAMS`.
```

- [ ] **Step 11: Commit**

```bash
git add scripts/compare_build.py tests/test_compare_build.py Makefile CLAUDE.md
git commit -m "build(config): add make compare against a base theme build

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01T8wJxhYYmrDNg3xDk819ma"
```

---

### Task 5: No JS, no third-party requests, budgets, deploy matcher coverage

**Files:**
- Create: `scripts/check_no_third_party.py`
- Test: `tests/test_check_no_third_party.py`
- Modify: `Makefile` (`audit:` recipe)
- Modify: `CLAUDE.md` (Automated checks list)

**Interfaces:**
- Produces:
  - `audit_html(text: str, label: str, max_css_bytes: int = MAX_INLINE_CSS_BYTES) -> list[str]`
  - `font_budget_errors(public_dir: Path, max_font_bytes: int = MAX_FONT_BYTES) -> list[str]`
  - `deploy_matcher_errors(public_dir: Path, hugo_toml: str) -> list[str]`
  - `audit_public(public_dir: Path, hugo_toml: str) -> list[str]`
  - CLI: `python3 scripts/check_no_third_party.py public hugo.toml`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_check_no_third_party.py`:

```python
from pathlib import Path

from scripts.check_no_third_party import (
    audit_html,
    deploy_matcher_errors,
    font_budget_errors,
)


def page(head: str = "", body: str = "") -> str:
    return f"<!doctype html><html><head>{head}</head><body>{body}</body></html>"


def test_accepts_local_resources_and_navigational_external_links() -> None:
    html = page(
        head=(
            "<style>@font-face{src:url(/fonts/f.woff2)}</style>"
            "<link rel=icon href=/favicon.svg>"
            "<link rel=preload href=/fonts/f.woff2 as=font>"
            "<link rel=canonical href=https://smallobservations.net/>"
            "<link rel=alternate type=application/rss+xml href=https://smallobservations.net/feed.xml>"
            "<link rel=me href=https://tilde.zone/@JonathanDeamer>"
            "<script type=application/ld+json>{}</script>"
        ),
        body=(
            '<img src=/img/a.jpg srcset="/img/a_200.webp 200w, /img/a_400.webp 400w">'
            "<a href=https://jonathandeamer.com>me</a>"
            '<span style="background:url(data:image/png;base64,AAAA)"></span>'
        ),
    )
    assert audit_html(html, "index.html") == []


def test_rejects_executable_script() -> None:
    assert audit_html(page(body="<script>alert(1)</script>"), "x.html") == [
        "x.html: <script> without type=application/ld+json"
    ]


def test_rejects_script_src_even_with_jsonld_type() -> None:
    errors = audit_html(page(body="<script type=application/ld+json src=/a.json></script>"), "x.html")
    assert errors == ["x.html: <script> with src=/a.json"]


def test_rejects_external_stylesheet_and_preconnect() -> None:
    html = page(
        head=(
            "<link rel=preconnect href=https://fonts.gstatic.com>"
            "<link rel=stylesheet href=https://fonts.googleapis.com/css2?family=Inter>"
        )
    )
    assert audit_html(html, "x.html") == [
        "x.html: <link rel=preconnect> loads off-site https://fonts.gstatic.com",
        "x.html: <link rel=stylesheet> loads off-site https://fonts.googleapis.com/css2?family=Inter",
    ]


def test_rejects_external_image_src_and_srcset() -> None:
    html = page(body='<img src=https://cdn.example.com/a.jpg srcset="/a.jpg 1x, https://cdn.example.com/b.jpg 2x">')
    assert audit_html(html, "x.html") == [
        "x.html: <img src> loads off-site https://cdn.example.com/a.jpg",
        "x.html: <img srcset> loads off-site https://cdn.example.com/b.jpg",
    ]


def test_rejects_embedding_elements() -> None:
    assert audit_html(page(body="<iframe src=/a.html></iframe>"), "x.html") == ["x.html: <iframe> not allowed"]


def test_rejects_css_import_and_external_url() -> None:
    html = page(head="<style>@import url(/a.css);body{background:url('https://example.com/bg.png')}</style>")
    assert audit_html(html, "x.html") == [
        "x.html: CSS @import not allowed",
        "x.html: CSS url() loads off-site https://example.com/bg.png",
    ]


def test_rejects_external_url_in_style_attribute() -> None:
    html = page(body='<div style="background:url(//example.com/a.png)"></div>')
    assert audit_html(html, "x.html") == ["x.html: CSS url() loads off-site //example.com/a.png"]


def test_css_budget() -> None:
    html = page(head="<style>" + "a{}" * 10 + "</style>")
    assert audit_html(html, "x.html", max_css_bytes=10) == [
        "x.html: inline CSS is 30 bytes (budget 10)"
    ]


def test_font_budget(tmp_path: Path) -> None:
    (tmp_path / "fonts").mkdir()
    (tmp_path / "fonts/a.woff2").write_bytes(b"x" * 8)
    (tmp_path / "fonts/b.woff2").write_bytes(b"x" * 8)
    assert font_budget_errors(tmp_path, max_font_bytes=16) == []
    assert font_budget_errors(tmp_path, max_font_bytes=15) == ["fonts/: 16 bytes (budget 15)"]


TOML = """
[[deployment.matchers]]
  pattern = "^.+\\\\.html$"
[[deployment.matchers]]
  pattern = "^.+\\\\.(?:woff2|woff)$"
"""


def test_every_file_needs_a_deploy_matcher(tmp_path: Path) -> None:
    for rel in ("index.html", "fonts/a.woff2", "fonts/a.otf", "favicon.ico", "robots.txt"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")
    assert deploy_matcher_errors(tmp_path, TOML) == [
        "fonts/a.otf: matches no [[deployment.matchers]] pattern (would deploy without Cache-Control)"
    ]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `make test`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.check_no_third_party'`.

- [ ] **Step 3: Write the implementation**

Create `scripts/check_no_third_party.py`:

```python
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


def deploy_matcher_errors(public_dir: Path, hugo_toml: str) -> list[str]:
    config = tomllib.loads(hugo_toml)
    patterns = [re.compile(m["pattern"]) for m in config.get("deployment", {}).get("matchers", [])]
    errors: list[str] = []
    for path in sorted(p for p in public_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(public_dir).as_posix()
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `make test`
Expected: all tests pass.

- [ ] **Step 5: Wire into audit and run against the real build**

In `Makefile`'s `audit:` recipe, directly after the `check_feed_sitemap.py` line and its following `@echo`, add:

```make
	@echo "→ no JS, no third-party requests, CSS/font budgets, deploy matchers:"
	@python3 scripts/check_no_third_party.py public hugo.toml
	@echo
```

Run: `make build && make audit; echo "exit=$?"`
Expected: the new section prints `    ok`, `exit=0`. If the real build reports an error, **stop and report it**. It means a current page already breaks the rule, and that's the user's decision, not something to fix by loosening the check.

- [ ] **Step 6: Document**

In `CLAUDE.md` under "Automated checks", add this bullet after the htmltest bullet:

```
- `check_no_third_party.py` fails on any executable `<script>` (only `application/ld+json` is allowed), any `<iframe>`/`<embed>`/`<object>`, any resource (`src`, `srcset`, non-navigational `<link>`, CSS `url()`) loaded from a host other than `smallobservations.net`, and any CSS `@import`. It also enforces budgets — inline CSS ≤ 16,000 bytes, `public/fonts/` ≤ 140,000 bytes — and requires every file in `public/` to match a `[[deployment.matchers]]` pattern (except `favicon.ico` and `robots.txt`), so a new file type can't ship without Cache-Control.
```

- [ ] **Step 7: Commit**

```bash
git add scripts/check_no_third_party.py tests/test_check_no_third_party.py Makefile CLAUDE.md
git commit -m "build(config): check no js, third-party loads, budgets, matchers

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01T8wJxhYYmrDNg3xDk819ma"
```

---

### Task 6: Page structure on every page type

**Files:**
- Create: `scripts/check_page_structure.py`
- Test: `tests/test_check_page_structure.py`
- Modify: `Makefile` (`audit:` recipe)
- Modify: `CLAUDE.md` (Automated checks list)

**Interfaces:**
- Produces:
  - `audit_page(text: str, label: str, public_dir: Path, is_home: bool) -> list[str]`
  - `audit_site(public_dir: Path) -> list[str]`
  - CLI: `python3 scripts/check_page_structure.py public`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_check_page_structure.py`:

```python
from pathlib import Path

from scripts.check_page_structure import audit_page, audit_site

HEAD = (
    "<title>t</title>"
    "<link rel=alternate type=application/rss+xml href=https://smallobservations.net/feed.xml>"
    "<link rel=icon type=image/svg+xml href=/favicon.svg>"
    "<link rel=icon type=image/x-icon href=/favicon.ico>"
    "<link rel=apple-touch-icon href=/apple-touch-icon.png>"
    "<link rel=preload href=/fonts/f.woff2 as=font type=font/woff2 crossorigin>"
    "<link rel=canonical href=https://smallobservations.net/x/>"
)
NAV = (
    '<nav class=masthead-browse aria-label="Browse the archive">'
    "<a href=/posts/>latest</a><a href=/tags/>tags</a><a href=/cities/>cities</a>"
    "<a href=/years/>years</a><a href=/countries/>countries</a><a href=/artists/>artists</a>"
    "</nav>"
)


def html(head: str = HEAD, body: str = "") -> str:
    return f"<!doctype html><html lang=en-gb><head>{head}</head><body>{body}</body></html>"


def home_body(img: str = "<img src=/a.jpg alt=a loading=eager fetchpriority=high>") -> str:
    return (
        "<a class=skip-nav href=#main-content>Skip to content</a>"
        "<main class=page id=main-content><header class=masthead>"
        "<a href=/><h1 class=masthead-title>Small<span>·</span>Observations</h1></a>"
        f"{NAV}</header><h2>A few favourites</h2>{img}<img src=/b.jpg alt=b loading=lazy></main>"
    )


def inner_body(main: str = "<h1>Tags</h1>") -> str:
    return (
        "<a class=skip-nav href=#main-content>Skip to content</a>"
        "<main class=page id=main-content><header class=masthead>"
        "<a href=/><p class=masthead-title>Small<span>·</span>Observations</p></a>"
        f"{NAV}</header>{main}</main>"
    )


def public(tmp_path: Path) -> Path:
    (tmp_path / "fonts").mkdir(exist_ok=True)
    (tmp_path / "fonts/f.woff2").write_bytes(b"x")
    return tmp_path


def test_accepts_valid_home_and_inner_pages(tmp_path: Path) -> None:
    pub = public(tmp_path)
    assert audit_page(html(body=home_body()), "index.html", pub, is_home=True) == []
    assert audit_page(html(body=inner_body()), "tags/index.html", pub, is_home=False) == []


def test_requires_exactly_one_h1(tmp_path: Path) -> None:
    pub = public(tmp_path)
    assert audit_page(html(body=inner_body("<h2>Tags</h2>")), "p.html", pub, False) == ["p.html: expected 1 <h1>, found 0"]
    assert audit_page(html(body=inner_body("<h1>A</h1><h1>B</h1>")), "p.html", pub, False) == [
        "p.html: expected 1 <h1>, found 2"
    ]


def test_site_title_is_h1_only_on_home(tmp_path: Path) -> None:
    pub = public(tmp_path)
    body = inner_body("").replace("<p class=masthead-title>", "<h1 class=masthead-title>").replace(
        "Observations</p>", "Observations</h1>"
    )
    assert audit_page(html(body=body), "p.html", pub, False) == [
        "p.html: site title must be <p class=masthead-title> on non-home pages",
        "p.html: <h1> must describe the page, not be the site title",
    ]
    home = home_body().replace("<h1 class=masthead-title>", "<h1>")
    assert audit_page(html(body=home), "index.html", pub, True) == [
        "index.html: home <h1> must be the site title (class masthead-title)"
    ]


def test_skip_link_must_be_first_and_target_main(tmp_path: Path) -> None:
    pub = public(tmp_path)
    body = "<div></div>" + inner_body()
    assert audit_page(html(body=body), "p.html", pub, False) == [
        "p.html: first element in <body> must be <a class=skip-nav href=#main-content>"
    ]
    body = inner_body().replace("<main class=page id=main-content>", "<div id=main-content>").replace("</main>", "</div>")
    assert audit_page(html(body=body), "p.html", pub, False) == ["p.html: #main-content must be a <main> element"]


def test_browse_nav_needs_all_six_links_and_label(tmp_path: Path) -> None:
    pub = public(tmp_path)
    body = inner_body().replace("<a href=/artists/>artists</a>", "").replace(' aria-label="Browse the archive"', "")
    assert audit_page(html(body=body), "p.html", pub, False) == [
        "p.html: <nav class=masthead-browse> needs an aria-label",
        "p.html: browse nav missing links to /artists/",
    ]


def test_head_links_required(tmp_path: Path) -> None:
    pub = public(tmp_path)
    head = HEAD.replace("<link rel=apple-touch-icon href=/apple-touch-icon.png>", "").replace(
        "https://smallobservations.net/feed.xml", "/index.xml"
    )
    assert audit_page(html(head=head, body=inner_body()), "p.html", pub, False) == [
        "p.html: RSS autodiscovery must point at https://smallobservations.net/feed.xml",
        "p.html: missing head link /apple-touch-icon.png",
    ]


def test_preload_targets_must_exist(tmp_path: Path) -> None:
    pub = public(tmp_path)
    head = HEAD.replace("/fonts/f.woff2", "/fonts/renamed.woff2")
    assert audit_page(html(head=head, body=inner_body()), "p.html", pub, False) == [
        "p.html: preload /fonts/renamed.woff2 does not exist in public/"
    ]


def test_home_first_image_wins_lcp(tmp_path: Path) -> None:
    pub = public(tmp_path)
    body = home_body(img="<img src=/a.jpg alt=a loading=lazy>")
    assert audit_page(html(body=body), "index.html", pub, True) == [
        "index.html: first <img> must have loading=eager and fetchpriority=high"
    ]


def test_audit_site_skips_alias_redirects_and_detects_home(tmp_path: Path) -> None:
    pub = public(tmp_path)
    (pub / "index.html").write_text(html(body=home_body()))
    alias = pub / "2022/11/old/index.html"
    alias.parent.mkdir(parents=True)
    alias.write_text(
        "<!doctype html><html><head><title>x</title>"
        "<meta http-equiv=refresh content=\"0; url=https://smallobservations.net/new/\"></head></html>"
    )
    assert audit_site(pub) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `make test`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.check_page_structure'`.

- [ ] **Step 3: Write the implementation**

Create `scripts/check_page_structure.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `make test`
Expected: all tests pass.

- [ ] **Step 5: Wire into audit and run against the real build**

In `Makefile`'s `audit:` recipe, directly after the `check_no_third_party.py` block, add:

```make
	@echo "→ page structure (h1, skip link, browse nav, head links, preloads):"
	@python3 scripts/check_page_structure.py public
	@echo
```

Run: `make build && make audit; echo "exit=$?"`
Expected: `    ok` for the new section, `exit=0`. If a real page fails (e.g. a pagination or by-count page missing a canonical), **stop and report it** with the error list. Don't weaken a rule without the user agreeing.

- [ ] **Step 6: Document**

In `CLAUDE.md` under "Automated checks", add:

```
- `check_page_structure.py` checks every non-alias HTML page for: exactly one `<h1>` (the site title on home, a page-specific heading elsewhere with the site title as `<p class="masthead-title">`); the skip link as first body element targeting a `<main id="main-content">`; the labelled browse nav with all six archive links; canonical, `/feed.xml` RSS autodiscovery and the favicon trio in `<head>`; every `rel=preload` target existing in `public/` (catches a renamed font); and `loading=eager` + `fetchpriority=high` on the homepage's first image.
```

- [ ] **Step 7: Commit**

```bash
git add scripts/check_page_structure.py tests/test_check_page_structure.py Makefile CLAUDE.md
git commit -m "build(config): check page structure invariants on every page

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01T8wJxhYYmrDNg3xDk819ma"
```

---

### Task 7: Microformats on post pages

**Files:**
- Create: `scripts/check_microformats.py`
- Test: `tests/test_check_microformats.py`
- Modify: `Makefile` (`audit:` recipe)
- Modify: `CLAUDE.md` (Automated checks list)

**Interfaces:**
- Produces:
  - `audit_post(text: str, label: str) -> list[str]`
  - `audit_posts(public_dir: Path) -> list[str]`
  - CLI: `python3 scripts/check_microformats.py public`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_check_microformats.py`:

```python
from pathlib import Path

from scripts.check_microformats import audit_post, audit_posts

POST = (
    "<!doctype html><html><head><title>t</title></head><body><main>"
    "<article class=\"post h-entry\">"
    "<h1 class=\"post-title p-name\">Brown bird</h1>"
    "<picture><img class=\"u-photo u-featured\" src=/img/a.jpg alt=a></picture>"
    "<p class=post-meta><time class=\"tnum dt-published\" datetime=2025-12-01T10:00:00Z>1 December 2025</time>"
    "<a rel=author class=\"p-author h-card\" href=https://jonathandeamer.com style=\"display: none;\">Jonathan Deamer</a>"
    "</article></main></body></html>"
)


def test_accepts_complete_h_entry() -> None:
    assert audit_post(POST, "p.html") == []


def test_requires_single_h_entry() -> None:
    assert audit_post(POST.replace("post h-entry", "post"), "p.html") == ["p.html: expected 1 h-entry, found 0"]


def test_requires_non_empty_name() -> None:
    assert audit_post(POST.replace(">Brown bird<", "><"), "p.html") == ["p.html: missing non-empty p-name"]


def test_name_may_be_visually_hidden() -> None:
    assert audit_post(POST.replace("post-title p-name", "post-title sr-only p-name"), "p.html") == []


def test_requires_photo_with_src() -> None:
    assert audit_post(POST.replace("u-photo u-featured", "photo"), "p.html") == ["p.html: missing <img class=u-photo src=...>"]


def test_requires_published_datetime() -> None:
    assert audit_post(POST.replace(" datetime=2025-12-01T10:00:00Z", ""), "p.html") == [
        "p.html: missing dt-published with datetime attribute"
    ]


def test_requires_author_card_with_href() -> None:
    assert audit_post(POST.replace("p-author h-card", "author"), "p.html") == [
        "p.html: missing p-author h-card with href"
    ]


def test_properties_must_follow_h_entry_start() -> None:
    moved = POST.replace("<article class=\"post h-entry\">", "").replace("</article>", "<div class=h-entry></div>")
    assert audit_post(moved, "p.html") == [
        "p.html: missing non-empty p-name",
        "p.html: missing <img class=u-photo src=...>",
        "p.html: missing dt-published with datetime attribute",
        "p.html: missing p-author h-card with href",
    ]


def test_audit_posts_skips_alias_redirects(tmp_path: Path) -> None:
    good = tmp_path / "2025/12/brown-bird/index.html"
    good.parent.mkdir(parents=True)
    good.write_text(POST)
    alias = tmp_path / "2025/12/old/index.html"
    alias.parent.mkdir(parents=True)
    alias.write_text("<html><head><meta http-equiv=refresh content=\"0; url=/x/\"></head></html>")
    assert audit_posts(tmp_path) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `make test`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.check_microformats'`.

- [ ] **Step 3: Write the implementation**

Create `scripts/check_microformats.py`:

```python
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
```

Note on `test_properties_must_follow_h_entry_start`: once the h-entry moves to the end, the `h-entry` div is the only element after `self.entries` becomes 1, so all four properties are missing. That's the behaviour the test pins.

- [ ] **Step 4: Run tests to verify they pass**

Run: `make test`
Expected: all tests pass.

- [ ] **Step 5: Wire into audit and run against the real build**

In `Makefile`'s `audit:` recipe, directly after the `check_page_structure.py` block, add:

```make
	@echo "→ post microformats (h-entry, p-name, u-photo, dt-published, p-author):"
	@python3 scripts/check_microformats.py public
	@echo
```

Run: `make build && make audit; echo "exit=$?"`
Expected: `    ok`, `exit=0`. If real posts fail, **stop and report**.

- [ ] **Step 6: Document**

In `CLAUDE.md` under "Automated checks", add:

```
- `check_microformats.py` requires every post page to carry exactly one `h-entry` followed by a non-empty `p-name`, an `<img class="u-photo">` with `src`, a `dt-published` with `datetime`, and a `p-author h-card` link. These classes share `class` attributes with styling classes, so a redesign that renames classes must keep them.
```

- [ ] **Step 7: Commit**

```bash
git add scripts/check_microformats.py tests/test_check_microformats.py Makefile CLAUDE.md
git commit -m "build(config): check h-entry microformats on post pages

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01T8wJxhYYmrDNg3xDk819ma"
```

---

### Task 8: End-to-end verification

**Files:** none changed unless a check misbehaves.

- [ ] **Step 1: Full test suite**

Run: `make test`
Expected: all tests pass. Report the count.

- [ ] **Step 2: Full check from clean**

Run: `make clean && make check; echo "exit=$?"`
Expected: every section `ok`/passed, `exit=0`.

- [ ] **Step 3: Compare against main and HEAD**

Run: `make compare; echo "exit=$?"; make compare BASE=HEAD; echo "exit=$?"`
Expected: both `ok`, both `exit=0`.

- [ ] **Step 4: Simulated redesign smoke test**

Run:
```bash
sed -i '' 's/--bg:       #f4ede0;/--bg:       #fbfaf7;/; s/--ink:      #1a1816;/--ink:      #111111;/' themes/notebook/assets/css/site.css
make build && make audit; echo "audit exit=$?"
make compare BASE=HEAD; echo "compare exit=$?"
git checkout themes/notebook/assets/css/site.css && make build
```
Expected: `compare exit=0`, because only CSS changed. `audit` may pass, or pa11y may report contrast issues from the new colours, which is the safety net working. Report which happened.

- [ ] **Step 5: Confirm the tree is clean**

Run: `git status --short`
Expected: no output.
