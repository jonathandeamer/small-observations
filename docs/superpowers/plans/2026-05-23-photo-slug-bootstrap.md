# Photo-Post Slug Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the `slug:` field of every photo post in `content/posts/*.md` to the `<city>-<editorial-hook>` shape defined in `docs/superpowers/specs/2026-05-23-photo-slug-bootstrap-design.md`, plus add a CLAUDE.md note pinning future slug changes to require `aliases:`.

**Architecture:** No automation. Per-post editorial judgment using existing front-matter (title, alt, tags, artists, cities). A small audit script enforces the structural invariants from the spec (shape, length, charset, uniqueness within year+month). Work proceeds in yearly batches with `make check` between commits. CLAUDE.md update lands separately so it survives even if the sweep is interrupted.

**Tech Stack:** Markdown front matter, `Edit` (exact string replacement), Python (audit script), `make build`/`make check`, `git`.

---

## Task 1: Load Spec Into Working Context

**Files:**
- Read: `docs/superpowers/specs/2026-05-23-photo-slug-bootstrap-design.md`
- Read: `CLAUDE.md` (for British English rule, commit format, taxonomy notes)

- [ ] **Step 1: Read the spec end-to-end**

The slug shape (`<city>-<editorial-hook>`), city normalization table, hook selection priority, drop rules, transliteration rules, length cap (70 chars), disambiguation policy, and worked examples must all be in working context for the entire pass.

- [ ] **Step 2: Read the worked examples carefully**

The eleven worked examples in the spec set the editorial taste. Re-read them mid-sweep if a judgment call feels uncertain.

## Task 2: Add the CLAUDE.md Future-Changes Rule

**Files:**
- Modify: `CLAUDE.md`

The spec commits us to using `aliases:` for any future slug change. CLAUDE.md needs to carry that rule so it survives the bootstrap and binds future work.

- [ ] **Step 1: Find the "Things that look wrong but aren't" section**

```bash
grep -n "^## Things that look wrong but aren't" CLAUDE.md
```

That section is the catch-all for non-obvious operational rules; the aliases rule belongs there.

- [ ] **Step 2: Add a new bullet at the end of that section**

Insert this bullet after the existing favicon/cache bullets, before the next `##` heading:

```markdown
- **Slug changes require aliases.** Photo-post slugs were bootstrapped once (see `docs/superpowers/specs/2026-05-23-photo-slug-bootstrap-design.md`). Any later rename to a post's `slug:` must add an `aliases:` front-matter entry pointing at the old URL path, so Hugo emits a 301 redirect and shared/indexed links keep working. The bootstrap pass itself was the only dispensation — site was soft-launched and barely indexed at the time.
```

- [ ] **Step 3: Commit the CLAUDE.md change**

```bash
git add CLAUDE.md
git commit -m "docs(config): require aliases for any future slug change"
```

## Task 3: Write the Slug Audit Script

**Files:**
- Create: `scripts/audit_slugs.py`

The script enforces the structural rules from the spec's Verification section. It does NOT judge editorial quality — that's the human's job — but it catches mechanical mistakes (wrong shape, illegal chars, length cap, year-month collisions).

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Audit photo-post slugs against the bootstrap spec.

Reports, for every post in content/posts/*.md:
  HARD violations (script exits non-zero):
    - slug missing
    - slug contains characters outside [a-z0-9-]
    - slug has leading/trailing hyphen or double hyphen
    - slug exceeds 70 characters
    - slug collides with another post in the same year+month bucket
  Soft warnings (printed, exit stays 0):
    - slug does not start with a known city prefix
    - slug is the legacy YYYY-MM-DD-<city> shape (not yet rewritten)
"""
from __future__ import annotations
import re, sys, pathlib
from collections import defaultdict

POSTS = pathlib.Path("content/posts")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
SLUG_CHARSET_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LEGACY_SHAPE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")

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
```

- [ ] **Step 2: Make it executable and run the baseline**

```bash
chmod +x scripts/audit_slugs.py
python3 scripts/audit_slugs.py | head -30
echo "Exit: $?"
```

Expected: every post will show `soft: slug '...' is the legacy YYYY-MM-DD-<city> shape (not yet rewritten)`. Exit 0 — no HARD violations yet because the legacy shape is well-formed.

- [ ] **Step 3: Commit**

```bash
git add scripts/audit_slugs.py
git commit -m "build(post): add slug audit script for bootstrap sweep"
```

## Task 4: Pilot — Rewrite Slugs for 10 Representative Posts

**Files (same 10 as the descriptions pilot, for editorial-taste continuity):**
- Modify: `content/posts/2005-09-02.md`
- Modify: `content/posts/2010-06-03-brighton.md`
- Modify: `content/posts/2016-04-15-dublin.md`
- Modify: `content/posts/2018-11-24-san-francisco.md`
- Modify: `content/posts/2019-07-09-bucuresti.md`
- Modify: `content/posts/2021-10-31-greater-london.md`
- Modify: `content/posts/2022-09-24-derbyshire-dales.md`
- Modify: `content/posts/2024-11-07-arrecife.md`
- Modify: `content/posts/2025-05-15-san-francisco.md`
- Modify: `content/posts/2026-01-21-city-of-london.md`

The same spread used for the descriptions pilot covers: ten different years, five countries, mixed forms (stencil, mural, sculpture, figure, installation), three named artists, and at least one cross-section quote-led post.

- [ ] **Step 1: Read each post's current front matter**

```bash
for f in 2005-09-02 2010-06-03-brighton 2016-04-15-dublin 2018-11-24-san-francisco 2019-07-09-bucuresti 2021-10-31-greater-london 2022-09-24-derbyshire-dales 2024-11-07-arrecife 2025-05-15-san-francisco 2026-01-21-city-of-london; do
  echo "=== $f ==="
  sed -n '/^---$/,/^---$/p' "content/posts/$f.md"
done
```

Note `title`, `slug` (current), `alt`, `tags`, `artists`, `cities`, `date` for each.

- [ ] **Step 2: For each post, draft the new slug per the spec**

Apply, in order:
1. City prefix from the spec's normalization table (or kebab-case of `cities[0]` if not listed).
2. Pick the highest-priority editorial anchor that the post genuinely has (named subject → quote → named artist → named theme → visual hook).
3. Apply drop rules: articles, prepositions, generic form nouns, generic adjectives, punctuation.
4. Transliterate diacritics.
5. Confirm 2–5 hook words, total slug ≤ 70 chars.

If two pilot posts collide in the same year+month, vary the second post's hook (don't append `-2`).

The expected new slugs for these ten posts, drawn from the worked examples in the spec plus the same rules applied to the other four:

| Post | Current slug | New slug |
|---|---|---|
| 2005-09-02 | `2005-09-02` | `seville-kurt-cobain` |
| 2010-06-03-brighton | `2010-06-03-brighton` | `brighton-james-brown` |
| 2016-04-15-dublin | `2016-04-15-dublin` | `dublin-niall-olochlainn-yes` |
| 2018-11-24-san-francisco | `2018-11-24-san-francisco` | `san-francisco-hella-resist` |
| 2019-07-09-bucuresti | `2019-07-09-bucuresti` | `bucharest-tangerines-are-better` |
| 2021-10-31-greater-london | `2021-10-31-greater-london` | `london-horace-halloween` |
| 2022-09-24-derbyshire-dales | `2022-09-24-derbyshire-dales` | `derbyshire-dales-burning-man-head` |
| 2024-11-07-arrecife | `2024-11-07-arrecife` | `arrecife-cubist-figure` |
| 2025-05-15-san-francisco | `2025-05-15-san-francisco` | `san-francisco-narcania-vs-death` |
| 2026-01-21-city-of-london | `2026-01-21-city-of-london` | `london-nathan-bowen-stay-positive` |

- [ ] **Step 3: Apply each edit with `Edit`**

One `Edit` per post. Replace only the `slug:` line. Do not touch any other front-matter field. Example for the first post:

```
Old: slug: "2005-09-02"
New: slug: "seville-kurt-cobain"
```

- [ ] **Step 4: Run the audit on the pilot subset**

```bash
for f in 2005-09-02 2010-06-03-brighton 2016-04-15-dublin 2018-11-24-san-francisco 2019-07-09-bucuresti 2021-10-31-greater-london 2022-09-24-derbyshire-dales 2024-11-07-arrecife 2025-05-15-san-francisco 2026-01-21-city-of-london; do
  python3 -c "
import sys; sys.path.insert(0, 'scripts')
from audit_slugs import audit_post
import pathlib
p = pathlib.Path('content/posts/$f.md')
hard, soft, _, _ = audit_post(p)
if hard or soft:
    print(p)
    for h in hard: print('  HARD:', h)
    for s in soft: print('  soft:', s)
"
done
```

Expected: zero HARD and zero soft for the ten pilot posts.

- [ ] **Step 5: Run `make build` to confirm the site still builds**

```bash
make build
```

Expected: exit 0. Hugo will rebuild URLs; nothing else should change.

- [ ] **Step 6: Sanity-check one new URL renders**

```bash
ls public/2005/09/seville-kurt-cobain/index.html
```

Expected: file exists. The old `public/2005/09/2005-09-02/` path will be gone (and that's intentional for this bootstrap — see the spec's no-aliases dispensation).

- [ ] **Step 7: Present the diff to the user for review**

```bash
git diff content/posts/
```

Wait for user feedback before any further posts are touched. If the user wants to adjust an editorial choice on the pilot, update the spec's worked examples too, then re-do the affected pilot posts.

- [ ] **Step 8: Commit once the user approves**

```bash
git add content/posts/2005-09-02.md content/posts/2010-06-03-brighton.md content/posts/2016-04-15-dublin.md content/posts/2018-11-24-san-francisco.md content/posts/2019-07-09-bucuresti.md content/posts/2021-10-31-greater-london.md content/posts/2022-09-24-derbyshire-dales.md content/posts/2024-11-07-arrecife.md content/posts/2025-05-15-san-francisco.md content/posts/2026-01-21-city-of-london.md
git commit -m "content(post): pilot rewrite of 10 slugs per bootstrap spec"
```

## Task 5: Sweep — Rewrite Slugs in Yearly Batches

**Files:**
- Modify: all remaining `content/posts/*.md` not touched in Task 4.

Years present in the archive: 2005, 2010, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026.

For each year batch, repeat steps 1–6 below.

- [ ] **Step 1: List the year's posts excluding pilot posts already done**

```bash
YEAR=2017   # change per batch
ls content/posts/${YEAR}-*.md
```

- [ ] **Step 2: Read each post's front matter and draft the new slug**

For each post: apply the same editorial discipline as the pilot. Mentally verify each hook word against `title`, `alt`, `tags`, `artists`. If two posts in the same year+month would collide, vary the later one's hook.

Use `Edit` to replace only the `slug:` line.

- [ ] **Step 3: Run the audit on the year batch**

```bash
YEAR=2017
for p in content/posts/${YEAR}-*.md; do
  python3 -c "
import sys; sys.path.insert(0, 'scripts')
from audit_slugs import audit_post
import pathlib
p = pathlib.Path('$p')
hard, soft, _, _ = audit_post(p)
if hard or soft:
    print(p)
    for h in hard: print('  HARD:', h)
    for s in soft: print('  soft:', s)
"
done
```

Expected: zero HARD. Soft warnings about the legacy shape are acceptable for posts you haven't yet rewritten *in other year batches*; within the current year batch every post should be clean. Investigate and fix any HARD violation before committing.

- [ ] **Step 4: Run `make build`**

```bash
make build
```

Expected: exit 0.

- [ ] **Step 5: Eyeball the diff**

```bash
git diff content/posts/${YEAR}-*.md
```

Look for: any slug whose hook you cannot defend against a source field; any slug that ended up too long; any slug that doesn't lead with the expected city prefix; any colliding slug within the year+month.

- [ ] **Step 6: Commit the year batch**

```bash
YEAR=2017
git add content/posts/${YEAR}-*.md
git commit -m "content(post): rewrite ${YEAR} slugs per bootstrap spec"
```

Repeat Task 5 for each remaining year.

## Task 6: Full-Archive Audit and `make check`

**Files:**
- Run: `scripts/audit_slugs.py`
- Run: `make check`

- [ ] **Step 1: Run the audit across all posts**

```bash
python3 scripts/audit_slugs.py
echo "Exit: $?"
```

Expected: exit 0. No HARD violations anywhere. The soft "legacy shape" warnings should be empty — every post has been rewritten. Soft "does not start with expected city prefix" warnings should be empty unless a post intentionally used a hook before its city (rare; document the reason in the commit if so).

- [ ] **Step 2: Spot-check 10 random new URLs in a browser**

Run the dev server and visit the new URLs manually:

```bash
make dev
```

Pick 10 random posts via:

```bash
ls content/posts/*.md | grep -v _index | sort -R | head -10 | while read p; do
  grep -E "^(date|slug):" "$p"
done
```

For each, construct the URL from `date.year`, `date.month`, `slug` and load it at `http://localhost:1313/<year>/<month>/<slug>/`. Confirm the post page renders, the photo loads, and the title is present. Stop the dev server when done.

- [ ] **Step 3: Run the full `make check`**

```bash
make check
```

Expected: exit 0. `htmltest` in particular will catch any internal link that still pointed at an old slug (taxonomy term pages link to posts, RSS feed lists posts, etc. — Hugo regenerates all of these so any breakage means a stale reference somewhere).

- [ ] **Step 4: Final commit if any audit-fix tweaks were made**

```bash
git add content/posts/
git commit -m "content(post): final audit fixes after slug bootstrap sweep"
```

(Skip if no changes since the last batch commit.)

## Self-review checklist for the rewriter (apply during Task 4 and Task 5)

For every slug you write:

1. Does it start with the city prefix from the spec table (or kebab-cased `cities[0]` if not listed)?
2. Is the hook 2–5 words?
3. Are all hook words derivable from `title`, `alt`, `tags`, `artists`, or `cities`?
4. Are articles (`a`, `the`, `of`, `on`, `in`, `at`, `with`, `by`) dropped unless they carry slogan weight?
5. Are generic form nouns (`mural`, `stencil`, `figure`, `painting`, `installation`, `sculpture`) dropped unless dropping them creates ambiguity?
6. Is total length ≤ 70 chars?
7. Is the slug unique within its year+month bucket?
8. Lowercase, `[a-z0-9-]+` only, no leading/trailing hyphen, no double hyphens?

If a slug fails any of 1, 2, 6, 7, 8 — fix it before moving on. If a slug fails 3, 4, or 5 — make an editorial judgment and document the reason in the batch commit message if it's non-obvious.
