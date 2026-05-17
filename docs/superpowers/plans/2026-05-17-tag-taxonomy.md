# Tag Taxonomy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the tag-taxonomy design from `docs/superpowers/specs/2026-05-17-tag-taxonomy-design.md` to every photo post under `content/posts/*.md`, deriving a complete, consistent `tags:` set from each post's alt text and body, and codify the conventions in `CLAUDE.md` for future authoring.

**Architecture:** Two commits in series. Commit 1 adds a "Tag taxonomy" section to `CLAUDE.md` codifying the rules. Commit 2 sweeps every post under `content/posts/*.md` (excluding `_index.md`), applies the derivation procedure to each, and writes the new `tags:` value back into the front matter in place. Path/front-matter ordering/other fields stay intact; only the `tags:` line changes (plus its addition where absent).

**Tech Stack:** Markdown, Hugo TOML/YAML front matter, `Edit` (in-place line replacement), `rg`, `sed`, `awk`, `git`. No image viewing — the derivation reads alt and body text only, which are already authoritative.

---

## Task 1: Codify Tag Conventions In CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (add a new section "Tag taxonomy" immediately after the existing "Content layers — when to reach for alt, tags, or body" section)

- [ ] **Step 1: Read the current CLAUDE.md to find the exact insertion point**

Locate the line `## Accessibility & web standards`. The new section goes immediately above it, after the "Content layers" section.

- [ ] **Step 2: Insert the Tag taxonomy section**

Use `Edit` with `old_string` set to the exact opening line `## Accessibility & web standards` and `new_string` set to the new section content followed by `\n## Accessibility & web standards`. The section content:

````markdown
## Tag taxonomy

The `tags` axis is a single bucket carrying four kinds of entry: **subjects** (what is depicted), **themes** (causes or movements the art engages with), **context** (named people/places/events referenced but not depicted, e.g. `John Lennon` on a "War is Over" piece), and **styles** (distinctive technique — `stencil`, `sticker`, `sculpture`, `Lichtenstein-style`, `Banksy-style`).

**Singletons are fine.** The bar is "plausible future category" — if it could imaginably recur, tag it. Expect the long-term set to sit at 150–250 tags with a long tail of singletons.

**Multi-level tagging.** When a post supports both a generic and a more specific term, tag both. Mural with a warbler → `bird`, `warbler`. Mural depicting the Beatles together → `Beatles`, `John Lennon`, `Paul McCartney`, `George Harrison`, `Ringo Starr`. Footballer in a Liverpool kit → `football`, `footballer`, `Liverpool FC`, `<player name>`.

**Generic floor — do not tag:** pure format (`mural`, `painted`, `graffiti`, `wall`, `street art`); generic body parts (`face`, `hand`, `eye`, `head`); generic colours and shapes (`blue`, `pink`, `circle`, `geometric`, plain `abstract`); loose adjectives (`bright`, `large`, `huge`, `small`, `colourful`).

**Naming conventions:**

| Tag kind | Convention | Examples |
|---|---|---|
| Common-noun subject | lowercase, singular | `bird`, `flamingo`, `skeleton`, `footballer`, `vampire` |
| Proper noun (person, team, place, event) | title case, as the world spells it | `John Lennon`, `Liverpool FC`, `Burning Man`, `Chinatown`, `Halloween`, `Barbican` |
| Movement or slogan | verbatim casing | `Black Lives Matter`, `Marriage Equality`, `Slava Ukraini`, `Abolish ICE` |
| Style descriptor | lowercase or title case to match the style's own usage | `stencil`, `sticker`, `sculpture`, `Lichtenstein-style`, `Banksy-style` |
| Theme without a canonical name | lowercase | `climate`, `anti-war`, `housing`, `memorial`, `protest`, `music` |

Pinned cases: `Beatles` not `The Beatles`; `Liverpool FC` not `LFC`; `stencil` (noun), not `stencilled`. Anything that already lives in `artists:`, `cities:`, `countries:`, or `years:` does NOT also need to be in `tags:` — those axes already exist for filtering.

**Deriving tags from a new post** (or auditing an existing one): work through the alt text and body text in this order: subjects depicted → themes engaged → context references → style → apply the floor (drop) → apply naming conventions → de-duplicate against existing tags (consult `/tags/` index to keep casing/spelling stable).

See `docs/superpowers/specs/2026-05-17-tag-taxonomy-design.md` for the full design and rationale.
````

- [ ] **Step 3: Verify the section landed cleanly**

Run:

```bash
grep -n "^## Tag taxonomy$" CLAUDE.md
grep -n "^## Accessibility & web standards$" CLAUDE.md
```

Expected: the two line numbers are present, with "Tag taxonomy" immediately before "Accessibility & web standards".

- [ ] **Step 4: Commit**

Run:

```bash
git add CLAUDE.md
git diff --cached --name-only
git commit -m "docs(config): codify tag taxonomy conventions"
```

Expected: only `CLAUDE.md` staged, commit succeeds.

## Task 2: Inventory Existing Tags

**Files:**
- Read: every `content/posts/*.md` except `_index.md`

- [ ] **Step 1: Capture every current `tags:` value**

Run:

```bash
mkdir -p tmp
grep -h '^tags:' content/posts/*.md \
  | sed 's/^tags: \[//;s/\]$//' \
  | tr ',' '\n' \
  | sed 's/^ *//;s/ *$//' \
  | grep -v '^$' \
  | sort | uniq -c | sort -rn > tmp/current-tags.txt
cat tmp/current-tags.txt
```

Expected: a counted list of all distinct existing tags (around 30 entries currently).

- [ ] **Step 2: Capture every current `artists:` value**

Run:

```bash
grep -h '^artists:' content/posts/*.md \
  | sed 's/^artists: \[//;s/\]$//' \
  | tr ',' '\n' \
  | sed 's/^ *//;s/ *$//' \
  | grep -v '^$' \
  | sort | uniq -c | sort -rn > tmp/current-artists.txt
cat tmp/current-artists.txt
```

Expected: a counted list of artists already populated. Anything here MUST NOT be duplicated in `tags:` later.

- [ ] **Step 3: Capture every post path with its alt and body for reference**

Run:

```bash
for f in content/posts/*.md; do
  [ "$(basename "$f")" = "_index.md" ] && continue
  echo "=== $f ==="
  awk '/^alt:/{print} /^---$/{c++; next} c==2 && NF{print}' "$f"
  echo
done > tmp/posts-content.txt
wc -l tmp/posts-content.txt
```

Expected: a single concatenated reference of 109 posts' alt and body content. Used as the source of truth for derivation in Task 3 — no need to re-read individual post files for content (only for replacing the `tags:` line).

## Task 3: Apply Derivation Procedure To All Posts

**Files:**
- Modify: every `content/posts/*.md` except `_index.md`

The derivation procedure (from the spec) is applied to each post in turn. For each post:

1. **Subjects depicted.** From alt text, every named or recognisable thing. Multi-level: generic plus specific where both are meaningful (e.g. `bird` + `warbler`).
2. **Themes engaged.** Causes, slogans, or movement language. Verbatim casing when the language appears in the artwork.
3. **Context references.** Named people/places/events pulled from BOTH alt text and body text (where present) that the artwork references but does not depict.
4. **Style.** Only when the style is distinctive and named — `stencil`, `sticker`, `sculpture`, `Banksy-style`, `Lichtenstein-style`, `comic-style`. Skip pure format words.
5. **Apply the floor.** Remove `mural`, `painted`, `graffiti`, `wall`, `face`, `hand`, `eye`, `head`, `blue`, `pink`, `circle`, `geometric`, plain `abstract`, `bright`, `large`, `huge`, `small`, `colourful`.
6. **Apply naming conventions** per the table in `CLAUDE.md`.
7. **De-duplicate** against `artists:`, `cities:`, `countries:`, `years:` for this same post — anything already there does not also belong in `tags:`.
8. **Preserve `favourite`** if the post had it. It is a hand-curated flag, not derivation output.

- [ ] **Step 1: Process posts in document order, one at a time**

For each post under `content/posts/*.md` (skipping `_index.md`):

1. Read the current file content (need the exact `tags:` line for the `Edit` call).
2. Derive the new tag set per the procedure above, drawing from the alt text and body text already captured in `tmp/posts-content.txt`.
3. Build the new `tags:` line as `tags: [<comma-and-space-separated entries>]` — Hugo's standard YAML flow-style array; matches the existing convention.
4. **Merge with existing tags rather than wholesale replacing.** Many existing tags encode context that the alt text alone cannot — local-knowledge place tags like `Parkland Walk` (18 posts), `Baltic Triangle`, `Barbican`; event/time tags like `Halloween`, `Liverpool Biennial`; and the hand-curated `favourite` flag. Preserve any existing tag that (a) does not violate the generic floor and (b) already matches the naming conventions or can be normalised to them (e.g. `Chinatown` not `China town`). The final set = (cleaned existing) ∪ (newly derived). If an existing tag both violates the floor AND duplicates an `artists:` / `cities:` / `countries:` / `years:` entry, drop it.
5. `Edit` the file: `old_string` = the entire current `tags:` line, `new_string` = the new `tags:` line. If the post currently has `tags: []`, the `old_string` is `tags: []` and the `new_string` is the populated list.
6. Verify the file still has exactly one `tags:` line.

Worked example (Brighton 2010, James Brown mural):

Alt text:
> A tall James Brown mural on the side of a building, with large red "JAMES BROWN" lettering, portraits, comic-style figures, and a speech bubble reading "That's because he's the Godfather."

Existing front matter:
- `cities: [Brighton]`, `artists: []`, `tags: [James Brown, music]`

Derivation:
1. Subjects: `James Brown` (depicted, named in the lettering). `music` (he is a musician, and "Godfather" references his music). No generic body subjects.
2. Themes: none — no cause/movement language.
3. Context: none beyond what's depicted.
4. Style: `comic-style` (alt text uses this phrase distinctively).
5. Floor: nothing to drop.
6. Naming: `James Brown` (title case, person), `music` (lowercase common noun), `comic-style` (lowercase style descriptor).
7. De-dup against other axes: `Brighton` is in `cities:`, no overlap.
8. `favourite`: not currently set, do not add.

New `tags:` line:

```
tags: [James Brown, music, comic-style]
```

`Edit` call:

- `old_string`: `tags: [James Brown, music]`
- `new_string`: `tags: [James Brown, music, comic-style]`

Worked example (the existing 9 viewed-and-named posts):

`2024-01-13-liverpool.jpg` (Ringo Starr portrait surrounded by Beatles/Yellow Submarine scenes):

- Subjects: `Beatles`, `John Lennon`, `Paul McCartney`, `George Harrison`, `Ringo Starr`, `music`
- Themes: none
- Context: `Yellow Submarine` (the Beatles film referenced)
- Style: none distinctive
- Floor: nothing
- Naming: title case for names, the Yellow Submarine entry
- De-dup: `Liverpool` in `cities:`; the band might be in `artists:` if they were the makers, but here they are subjects of the mural, so they belong in `tags:`. Confirm `artists:` does not contain `The Beatles` for this post; if it does, the band names go in `artists:` only.

New `tags:` line:

```
tags: [Beatles, John Lennon, Paul McCartney, George Harrison, Ringo Starr, music, Yellow Submarine]
```

- [ ] **Step 2: Process the remaining 108 posts following the same procedure**

Iterate. The full set of posts is the file list under `content/posts/*.md` minus `_index.md`. Take the alt and body content from `tmp/posts-content.txt` (already captured in Task 2). For each post, build the derived `tags:` set and apply the `Edit`.

Maintain an in-flight canonical list (mental or in `tmp/canonical-tags.txt`) of every tag spelled-and-cased exactly as it should appear, so the casing stays consistent across all 109 posts. If you encounter a candidate that is a casing variant of one already used (e.g. `the beatles` vs the canonical `Beatles`), use the canonical form.

- [ ] **Step 3: Update the canonical list reference**

Run:

```bash
grep -h '^tags:' content/posts/*.md \
  | sed 's/^tags: \[//;s/\]$//' \
  | tr ',' '\n' \
  | sed 's/^ *//;s/ *$//' \
  | grep -v '^$' \
  | sort | uniq -c | sort -rn > tmp/new-tags.txt
diff tmp/current-tags.txt tmp/new-tags.txt | head -60
wc -l tmp/new-tags.txt
```

Expected: `wc -l` reports somewhere between 150 and 250. The `diff` shows the change (many additions, some renames).

## Task 4: Verify The Result

**Files:**
- Read: every `content/posts/*.md` and `tmp/new-tags.txt`

- [ ] **Step 1: Every post has a `tags:` line and it parses**

Run:

```bash
missing=0
for f in content/posts/*.md; do
  [ "$(basename "$f")" = "_index.md" ] && continue
  grep -q '^tags:' "$f" || { echo "MISSING tags: $f"; missing=$((missing+1)); }
done
echo "missing=$missing"
```

Expected: `missing=0`.

- [ ] **Step 2: No generic-floor tags slipped through**

Run:

```bash
rg -wn -E 'mural|painted|graffiti|wall|street art|face|hand|eye|head|colourful|bright|large|huge|small' tmp/new-tags.txt || echo "clean"
```

Expected: `clean`. (The regex tests against the tag list only, not the alt text.)

- [ ] **Step 3: No casing duplicates**

Confirm that no tag exists in two different casings (e.g. both `Beatles` and `beatles`):

```bash
awk '{print tolower($2)}' tmp/new-tags.txt | sort | uniq -d
```

Expected: no output. If anything appears, fix the variant in the affected post(s) and re-run.

- [ ] **Step 4: No tag duplicates an artist on the same post**

Run:

```bash
clash=0
for f in content/posts/*.md; do
  [ "$(basename "$f")" = "_index.md" ] && continue
  artists=$(awk -F'[][]' '/^artists:/{print $2}' "$f" | tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep -v '^$')
  tags=$(awk -F'[][]' '/^tags:/{print $2}' "$f" | tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep -v '^$')
  while IFS= read -r a; do
    [ -z "$a" ] && continue
    echo "$tags" | grep -qFx "$a" && { echo "CLASH in $f: $a"; clash=$((clash+1)); }
  done <<< "$artists"
done
echo "clash=$clash"
```

Expected: `clash=0`.

- [ ] **Step 5: `make build` succeeds and `make check` passes**

Run:

```bash
make build 2>&1 | tail -8
```

Expected: build completes with no errors. Then:

```bash
make check 2>&1 | grep -E '→|ok|valid|WARNING|INVALID|MISSING|issues found' | head -20
```

Expected: pa11y still passes; sitemap ok; RSS ok; no new warnings introduced.

## Task 5: Commit

**Files:**
- Commit: every modified `content/posts/*.md`
- Do not stage: anything else (the `tmp/` directory is gitignored; `tmp/current-tags.txt`, `tmp/posts-content.txt`, `tmp/new-tags.txt`, `tmp/canonical-tags.txt` stay local)

- [ ] **Step 1: Review the scoped diff**

Run:

```bash
git status --short
git diff --stat content/posts/ | tail -5
```

Expected: only `content/posts/*.md` files are modified; no other paths.

- [ ] **Step 2: Stage and commit**

Run:

```bash
git add content/posts/
git diff --cached --name-only | head -5
git commit -m "content(post): apply tag taxonomy across all photo posts"
```

Expected: commit succeeds, hook passes, only `content/posts/*.md` files included.

- [ ] **Step 3: Report**

Print a one-line summary of the change: number of posts modified, before/after tag count, any cases that were judgement calls worth flagging.
