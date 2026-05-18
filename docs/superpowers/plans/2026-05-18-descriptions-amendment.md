# Photo-Post Descriptions Amendment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the `description:` field of every photo post in `content/posts/*.md` to follow the new shape in `docs/superpowers/specs/2026-05-18-descriptions-amendment-design.md`, and apply narrow title cleanup where titles hit the spec's three criteria.

**Architecture:** Pilot first (10 hand-picked posts), review with user, refine spec if needed, then sweep remaining posts in yearly batches. A small audit script enforces the greppable invariants from the spec's verification section. `make check` confirms the build still passes after each batch.

**Tech Stack:** Markdown front matter, `Edit` (exact string replacement), Python (audit script), `make check`, `git`.

---

## Task 1: Load Spec and Prior Spec Into Working Context

**Files:**
- Read: `docs/superpowers/specs/2026-05-18-descriptions-amendment-design.md`
- Read: `docs/superpowers/specs/2026-05-17-titles-descriptions-design.md`

- [ ] **Step 1: Read both specs end-to-end**

The amendment defines the new description shape and title cleanup criteria. The prior spec defines the grounding rule ("Source discipline"), voice, and the parts that are unchanged. Both must be in context for the entire pass.

- [ ] **Step 2: Confirm understanding of the form-word vocabulary**

The preferred vocabulary is: mural, stencil, sticker, sculpture, installation, painting, portrait, figure, scene, sign. `"Photo of…"` is a fallback only. Each form word picked for a description must be defensible against the post's alt text.

## Task 2: Write the Audit Script

**Files:**
- Create: `scripts/audit_descriptions.py`

The script enforces the greppable invariants from the spec's Verification section. Used after every batch (and during the pilot) to catch regressions.

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Audit photo-post descriptions against the amendment spec.

Reports, for every post in content/posts/*.md:
  - description begins with "Photo of" (allowed only as fallback; flag for review)
  - description length > 160 chars
  - description missing the post's year (date.year)
  - description ends with ", in <City>." where <City> is already in title
  - title ends with a neighbourhood-like trailing token not in cities/countries
    (heuristic: trailing token after the last comma not equal to any cities[] entry)

Exit non-zero if any HARD violations (length, missing year) are present.
Soft warnings ("Photo of", trailing-city, neighbourhood) are printed but don't fail.
"""
from __future__ import annotations
import re, sys, pathlib

POSTS = pathlib.Path("content/posts")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

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

def year_from_date(date_str: str) -> str | None:
    m = re.match(r"(\d{4})", date_str.strip())
    return m.group(1) if m else None

def audit_post(path: pathlib.Path) -> tuple[list[str], list[str]]:
    text = path.read_text()
    fm = parse_front_matter(text)
    title = strip_quotes(fm.get("title", ""))
    desc = strip_quotes(fm.get("description", ""))
    cities = parse_list(fm.get("cities", "[]"))
    year = year_from_date(fm.get("date", ""))

    hard, soft = [], []
    if len(desc) > 160:
        hard.append(f"description length {len(desc)} > 160")
    if year and year not in desc:
        hard.append(f"description missing year {year}")
    if desc.lower().startswith("photo of"):
        soft.append("description starts with 'Photo of' (fallback only)")
    for city in cities:
        if city and f", in {city}." in desc and city in title:
            soft.append(f"description ends with city '{city}' already in title")
    if "," in title:
        trailing = title.rsplit(",", 1)[1].strip()
        if trailing and trailing not in cities and trailing not in parse_list(fm.get("countries", "[]")):
            soft.append(f"title ends with '{trailing}' (not in cities/countries — neighbourhood?)")
    return hard, soft

def main() -> int:
    exit_code = 0
    posts = sorted(p for p in POSTS.glob("*.md") if p.name != "_index.md")
    for p in posts:
        hard, soft = audit_post(p)
        if hard or soft:
            print(f"\n{p}")
            for h in hard:
                print(f"  HARD: {h}")
                exit_code = 1
            for s in soft:
                print(f"  soft: {s}")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Make it executable and run it on the current state**

```bash
chmod +x scripts/audit_descriptions.py
python3 scripts/audit_descriptions.py | head -50
```

Expected: every post will show `soft: description starts with 'Photo of'` and most will show `soft: description ends with city '<X>' already in title`. The script should exit 0 (no HARD violations yet — current descriptions are within length and do contain their year contexts? Likely not — current descriptions do NOT contain the year. So most posts WILL show `HARD: description missing year`).

This baseline is fine — it confirms the script works and shows what the sweep needs to fix.

- [ ] **Step 3: Commit**

```bash
git add scripts/audit_descriptions.py
git commit -m "build(post): add description audit script for amendment sweep"
```

## Task 3: Pilot — Rewrite 10 Representative Posts

**Files:**
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

The 10 posts span years 2005–2026, five countries, and a mix of forms (stencil, mural, figure, installation, sculpture). Three have named artists; several do not. One (`2025-05-15-san-francisco.md`) has a title ending in a neighbourhood (`Clarion Alley`) — title cleanup will be exercised here.

- [ ] **Step 1: Read each post's current front matter**

```bash
for f in 2005-09-02 2010-06-03-brighton 2016-04-15-dublin 2018-11-24-san-francisco 2019-07-09-bucuresti 2021-10-31-greater-london 2022-09-24-derbyshire-dales 2024-11-07-arrecife 2025-05-15-san-francisco 2026-01-21-city-of-london; do
  echo "=== $f ==="
  sed -n '/^---$/,/^---$/p' "content/posts/$f.md" | head -25
  echo
done
```

Note for each post: `title`, `description`, `alt`, `cities`, `artists`, `tags`, `date.year`, and any body text after the closing `---`.

- [ ] **Step 2: For each post, draft the new title (if cleanup-eligible) and new description**

Apply the spec's grounding rule. For each substantive claim in the new title/description, identify the source field in the front matter. If a claim has no source, drop it. Use the worked examples in the spec as the editorial reference.

For `2025-05-15-san-francisco.md`: title currently ends in `Clarion Alley` (neighbourhood). Fix per the spec's title cleanup criterion #1 — either restore the city (`, Clarion Alley, San Francisco`) or fold the neighbourhood into the subject. Pick whichever reads more naturally.

For the other nine posts: title remains unchanged; description is rewritten.

- [ ] **Step 3: Apply each edit with `Edit`**

One `Edit` per post. Replace only the `description:` line (and `title:` line for the cleanup-eligible post). Do not touch other front-matter fields.

- [ ] **Step 4: Run the audit on the pilot subset**

```bash
for f in 2005-09-02 2010-06-03-brighton 2016-04-15-dublin 2018-11-24-san-francisco 2019-07-09-bucuresti 2021-10-31-greater-london 2022-09-24-derbyshire-dales 2024-11-07-arrecife 2025-05-15-san-francisco 2026-01-21-city-of-london; do
  python3 -c "
import sys; sys.path.insert(0, 'scripts')
from audit_descriptions import audit_post
import pathlib
p = pathlib.Path('content/posts/$f.md')
hard, soft = audit_post(p)
if hard or soft:
    print(p)
    for h in hard: print('  HARD:', h)
    for s in soft: print('  soft:', s)
"
done
```

Expected: zero HARD violations across the 10 posts. Soft warnings about `"Photo of"` should be gone. Soft warnings about trailing city should be gone unless the description deliberately keeps a neighbourhood/landmark detail.

- [ ] **Step 5: Run `make build` to confirm the site still builds**

```bash
make build
```

Expected: exit 0, no errors.

- [ ] **Step 6: Present the diff to the user for review**

```bash
git diff content/posts/
```

Show the diff. Wait for user feedback before any further posts are touched. If the user wants spec changes, update the spec and re-do the affected pilot posts.

- [ ] **Step 7: Commit once the user approves**

```bash
git add content/posts/2005-09-02.md content/posts/2010-06-03-brighton.md content/posts/2016-04-15-dublin.md content/posts/2018-11-24-san-francisco.md content/posts/2019-07-09-bucuresti.md content/posts/2021-10-31-greater-london.md content/posts/2022-09-24-derbyshire-dales.md content/posts/2024-11-07-arrecife.md content/posts/2025-05-15-san-francisco.md content/posts/2026-01-21-city-of-london.md
git commit -m "content(post): pilot rewrite of 10 descriptions per amendment spec"
```

## Task 4: Sweep — Rewrite Remaining Posts in Yearly Batches

**Files:**
- Modify: all remaining `content/posts/*.md` not touched in Task 3.

Sweep one year at a time. Years present in the archive: 2005, 2010, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025, 2026. (Confirm with `ls content/posts/ | cut -c1-4 | sort -u`.)

For each year batch, repeat steps 1–6 below.

- [ ] **Step 1: List the year's posts excluding pilot posts already done**

```bash
YEAR=2017   # change per batch
ls content/posts/${YEAR}-*.md
```

- [ ] **Step 2: Read each post's front matter and rewrite its description**

For each post, follow the same grounding discipline as the pilot. Use `Edit` to replace only the `description:` line (and `title:` line if and only if the title hits one of the three cleanup criteria from the spec).

- [ ] **Step 3: Run the audit on the year batch**

```bash
YEAR=2017
for p in content/posts/${YEAR}-*.md; do
  python3 -c "
import sys; sys.path.insert(0, 'scripts')
from audit_descriptions import audit_post
import pathlib
p = pathlib.Path('$p')
hard, soft = audit_post(p)
if hard or soft:
    print(p)
    for h in hard: print('  HARD:', h)
    for s in soft: print('  soft:', s)
"
done
```

Expected: zero HARD violations. Investigate and fix any HARD before committing.

- [ ] **Step 4: Run `make build`**

```bash
make build
```

Expected: exit 0.

- [ ] **Step 5: Eyeball the diff**

```bash
git diff content/posts/${YEAR}-*.md | less
```

Look for: any phrase you cannot point to a source field for; any description still reading as a restatement of the title; any descriptions ending in a city that's already in the title; any description without a year.

- [ ] **Step 6: Commit the year batch**

```bash
YEAR=2017
git add content/posts/${YEAR}-*.md
git commit -m "content(post): rewrite ${YEAR} descriptions per amendment spec"
```

Repeat Task 4 for each remaining year.

## Task 5: Full-Archive Audit and `make check`

**Files:**
- Run: `scripts/audit_descriptions.py`
- Run: `make check`

- [ ] **Step 1: Run the audit across all posts**

```bash
python3 scripts/audit_descriptions.py
echo "Exit: $?"
```

Expected: exit 0 (no HARD violations). Soft warnings about `"Photo of"` are acceptable only for posts where no form word in the preferred vocabulary fits the alt — review each such case and confirm the fallback is justified.

- [ ] **Step 2: Spot-check 10 random posts for restatement**

```bash
ls content/posts/*.md | grep -v _index | shuf -n 10 | while read p; do
  echo "=== $p ==="
  grep -E "^(title|description):" "$p"
  echo
done
```

For each pair, ask: read together as a Slack/Twitter share card, do title and description say different things? If three or more pairs still read as restatements, the spec or the sweep needs another pass — go back to the user before declaring done.

- [ ] **Step 3: Run the full `make check`**

```bash
make check
```

Expected: exit 0. `pa11y`, `htmltest`, `xmllint`, and `vnu` all pass.

- [ ] **Step 4: Final commit if any audit-fix tweaks were made**

```bash
git add content/posts/
git commit -m "content(post): final audit fixes after amendment sweep"
```

(Skip if no changes since the last batch commit.)

## Self-review checklist for the rewriter (apply during Task 3 and Task 4)

For every description you write:

1. Can you underline the form word in the alt? If no, use `"Photo of…"` or pick a different form word.
2. Does the description contain the year from `date`? If no, add it.
3. Is the description ≤160 chars? If no, trim.
4. Does the description end with `, in <City>.` where `<City>` is in the title? If yes, drop it.
5. Read title and description back-to-back. Do they say different things? If no, rewrite the description with a different distinguishing detail.
6. For every substantive phrase in the description, name the source field (alt / artists / tags / body / date). If a phrase has no source, drop it.
