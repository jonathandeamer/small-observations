# Page Titles and Descriptions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Populate `title:`, `description:` (and optional `headline:`) front matter across all 109 photo posts, all ~149 taxonomy term pages, the 6 taxonomy index pages, and the section/special pages — so every page emits a unique, grounded `<title>` / `<meta description>` / OG / Twitter / RSS payload.

**Architecture:** Five sequential commits. The first is a small template tweak that introduces SR-only fallback rendering for the `title:` field and visible rendering for the new `headline:` field. The four remaining commits write content in distinct slices (posts; tag term pages; other taxonomy term pages; indexes + section pages). Each subagent dispatch handles one slice end-to-end (inventory → write → verify → commit) using strict source rules from the spec.

**Tech Stack:** Hugo 0.161.1, hand-written Markdown front matter, hand-written prose, no JavaScript. Bash + grep + sed for inventory.

> The spec at `docs/superpowers/specs/2026-05-17-titles-descriptions-design.md` is the source of truth for source rules, voice, length targets, and per-page-type shape. Each task below quotes the rules verbatim so implementers don't need to re-read the spec — but reading it once for full context is recommended.

---

## Task 1: Template change — `headline:` visible + SR-only `title:` fallback

**Files:**
- Modify: `themes/notebook/layouts/_default/single.html`

- [ ] **Step 1: Make the edit**

Use `Edit` with:

- `old_string`:

```
  {{ with .Title }}<h2 class="post-title">{{ . }}</h2>{{ end }}
```

- `new_string`:

```
  {{ if .Params.headline }}
    <h2 class="post-title">{{ .Params.headline }}</h2>
  {{ else if .Title }}
    <h2 class="post-title sr-only">{{ .Title }}</h2>
  {{ end }}
```

This produces three rendering states:
- `headline:` set → visible `<h2>` of the headline.
- `headline:` empty, `title:` set → SR-only `<h2>` of the title (visually hidden via the existing `.sr-only` utility).
- Both empty → no `<h2>` element (matches today's behaviour; safety for any post that lacks both during the migration).

- [ ] **Step 2: Verify the template renders for both states**

Run:

```bash
make build 2>&1 | tail -3
```

Expected: build succeeds (note: most posts still have neither field set, so the visible page should look unchanged at this point).

- [ ] **Step 3: Spot-check the rendered HTML against the no-title state**

Run:

```bash
grep -c '<h2' public/2010/06/2010-06-03-brighton/index.html
```

Expected: 0 (no `<h2>` because the Brighton post has neither `headline:` nor `title:` set yet).

- [ ] **Step 4: Commit**

Run:

```bash
git add themes/notebook/layouts/_default/single.html
git commit -m "feat(post): support headline and sr-only title h2 fallback"
```

## Task 2: Write `title:` and `description:` for all 109 photo posts

**Files:**
- Modify: every `content/posts/*.md` except `_index.md`

Source-strict rules (verbatim from the spec):

**Permitted sources:** `alt:`, body text, `tags:`, `artists:`, `cities:`, `countries:`, `years:`, `date:`, `exif.camera`.

**Forbidden:** looking at the image, external knowledge about depicted people/places/movements/styles, inferring neighbourhoods from coordinates, evaluative or aesthetic framing, editorialising.

**Voice:** observational, modest, British spellings.

**Length targets:**
- `title:` 35–60 chars (hard ceiling 70)
- `description:` 100–120 chars (hard ceiling 140)
- `headline:` (optional) 25–50 chars (hard ceiling 60)

**Shape:**

- `title:` — distinctive subject + location/attribution. Sentence-cased, no full stop. Examples (each citable to real alts in this archive):
  - "Vampire mural, Liverpool"
  - "Ringo Starr in Yellow Submarine scenes, Liverpool"
  - "Picasso portrait on a corrugated door, Barcelona"
  - "Chuck Berry stencil, London"
  - "Memorial mural for George Floyd and Breonna Taylor, San Francisco"

- `description:` — leads with **"Photo of"** prefix, then one sentence covering scene + anchor (location, year, artist, or context). Examples:
  - "Photo of a purple vampire holding a lit candle in front of a full moon, on a brick wall in Liverpool."
  - "Photo of a Banksy-style stencil of two officers searching a Basquiat-style crowned figure, on Golden Lane in London."
  - "Photo of a memorial mural for George Floyd and Breonna Taylor with portraits and Black Lives Matter signs, in San Francisco's Clarion Alley."

- `headline:` — only if the post genuinely warrants a visible heading. Most posts leave this empty. The bar: "would I want a reader to read this before looking at the photo?"

Insertion point in front matter: between `photo:` and `alt:`, so the order becomes `photo` → `title` → `headline` (when present) → `alt` → `description` → other fields. (Existing convention is single-line YAML inline arrays; preserve that.)

Worked example for `content/posts/2010-06-03-brighton.md`:

Current front matter (relevant lines):
```yaml
photo: 2010/06/2010-06-03-brighton.jpg
alt: "A tall James Brown mural on the side of a building, with large red \"JAMES BROWN\" lettering, portraits, comic-style figures, and a speech bubble reading \"That's because he's the Godfather.\""
cities: [Brighton]
```

Adds:
```yaml
photo: 2010/06/2010-06-03-brighton.jpg
title: "James Brown mural, Brighton"
alt: "A tall James Brown mural on the side of a building..."
description: "Photo of a tall James Brown mural with red \"JAMES BROWN\" lettering, portraits, and a speech bubble, in Brighton."
```

Citation trace:
- "James Brown mural" → alt names James Brown
- "Brighton" → `cities: [Brighton]`
- "red 'JAMES BROWN' lettering" / "portraits" / "speech bubble" → alt
- Length: title 28 chars, description 130 chars ✓

- [ ] **Step 1: Process each post atomically**

For each post under `content/posts/*.md` (skip `_index.md`):

1. Read the file. Note `alt:`, body text (if any), `tags:`, `artists:`, `cities:`, `countries:`, `years:`, `date:`.
2. Draft `title:` per the shape and length rules. Trace every word to a source. Adjust until under 60 chars.
3. Draft `description:` per the shape and length rules. Trace every phrase to a source.
4. Decide whether `headline:` is warranted; usually no.
5. Use `Edit` to insert the new lines into front matter at the canonical position (after `photo:`, in the order `title` → `headline` → `alt` → `description`). If the file already has a `title: ""` line, replace it with the new value rather than adding a new line.
6. Verify length and source-tracing before moving on.

- [ ] **Step 2: Verify all 109 posts have populated title + description**

Run:

```bash
missing=0
for f in content/posts/*.md; do
  [ "$(basename "$f")" = "_index.md" ] && continue
  grep -q '^title: ".\+"' "$f" || { echo "no title: $f"; missing=$((missing+1)); }
  grep -q '^description: ".\+"' "$f" || { echo "no description: $f"; missing=$((missing+1)); }
done
echo "missing=$missing"
```

Expected: `missing=0`.

- [ ] **Step 3: Verify all descriptions lead with "Photo of"**

Run:

```bash
bad=0
for f in content/posts/*.md; do
  [ "$(basename "$f")" = "_index.md" ] && continue
  desc=$(grep '^description:' "$f" | sed 's/^description: *"//;s/"$//')
  case "$desc" in
    "Photo of "*) ;;
    *) echo "no Photo-of prefix: $f -- $desc"; bad=$((bad+1));;
  esac
done
echo "bad=$bad"
```

Expected: `bad=0`.

- [ ] **Step 4: Verify length ceilings**

Run:

```bash
for f in content/posts/*.md; do
  [ "$(basename "$f")" = "_index.md" ] && continue
  title=$(grep '^title:' "$f" | sed 's/^title: *"//;s/"$//')
  desc=$(grep '^description:' "$f" | sed 's/^description: *"//;s/"$//')
  [ ${#title} -gt 70 ] && echo "title >70 ($((${#title}))): $f -- $title"
  [ ${#desc} -gt 140 ] && echo "desc >140 ($((${#desc}))): $f -- $desc"
done
```

Expected: no output.

- [ ] **Step 5: Build and check**

Run:

```bash
make build 2>&1 | tail -5
```

Expected: build succeeds.

- [ ] **Step 6: Commit**

Run:

```bash
git add content/posts/
git commit -m "content(post): write titles and descriptions for all photo posts"
```

## Task 3: Write descriptions for tag term pages (~99 files)

**Files:**
- Create: one `content/tags/<term-slug>/_index.md` per tag term

Hugo doesn't auto-generate term-page content files; we add `_index.md` files to set `description:` per term. The `title:` in these files is decorative (Hugo's taxonomy renders the term name as the page title regardless) but included for self-explanation.

**Shape** (verbatim from spec):

Prefix: "Street art photos tagged `<term>`"

Optionally followed by an em-dash and grounded flavour drawn from posts that carry this tag — examples / themes / a one-clause characterisation. Each phrase in the flavour clause must be citable to actual posts with that tag.

Examples:
- "Street art photos tagged birds — pink flamingos, a snowy owl pair, an abstract NHS bird, and others."
- "Street art photos tagged protest — slogans, banners, calls to action."
- "Street art photos tagged stencil — quick high-contrast pieces, often political."
- "Street art photos tagged John Lennon — murals depicting him, plus pieces referencing his lyrics."

Bare-template is acceptable when there isn't enough grounded material:
- "Street art photos tagged Brexit."

**Length:** 80–140 chars target, 160 ceiling.

- [ ] **Step 1: Build the list of distinct tags with their slugs and post lists**

Run:

```bash
mkdir -p tmp
# Distinct tag values (preserving case):
grep -h '^tags:' content/posts/*.md \
  | sed 's/^tags: \[//;s/\]$//' \
  | tr ',' '\n' | sed 's/^ *//;s/ *$//' \
  | grep -v '^$' | sort -u > tmp/tag-values.txt
wc -l tmp/tag-values.txt
```

Expected: ~99 lines.

- [ ] **Step 2: Create one `_index.md` per term**

For each tag value in `tmp/tag-values.txt`:

1. Compute the slug Hugo will use. Hugo lowercases and replaces non-alphanumerics with `-`. For example `Black Lives Matter` → `black-lives-matter`; `Liverpool FC` → `liverpool-fc`; `John Lennon` → `john-lennon`; `Día de Muertos` → `dia-de-muertos`.
2. Find all posts carrying that tag:

```bash
grep -l "^tags:.*\b<term>\b" content/posts/*.md
```

Or more precisely with case-sensitive match for proper-noun tags.

3. Read the alts of those posts (up to ~5 representative ones).
4. Compose the description following the shape and length rules. Trace every phrase in the flavour clause to a citable source.
5. Write the file to `content/tags/<slug>/_index.md`:

```yaml
---
title: "<Original tag value>"
description: "<Composed description>"
---
```

Example for the `birds` tag — write `content/tags/birds/_index.md`:

```yaml
---
title: "birds"
description: "Street art photos tagged birds — pink flamingos, a snowy owl pair, an abstract NHS bird, and others."
---
```

The flavour clause "pink flamingos, a snowy owl pair, an abstract NHS bird" is citable: there are posts tagged `flamingo`+`birds` describing pink flamingos, a 2022-11-15-brighton post about snowy owls, and a 2021-07-02 NHS-bird post.

- [ ] **Step 3: Verify all tag terms have an `_index.md`**

Run:

```bash
# Count tag-values vs created _index.md files
echo "tag values: $(wc -l < tmp/tag-values.txt)"
echo "_index.md files: $(find content/tags -mindepth 2 -name '_index.md' | wc -l)"
```

Expected: both counts equal (one `_index.md` per unique tag).

If counts differ, list the missing terms:

```bash
# Slugify tag values and compare to existing dirs
while read tag; do
  slug=$(echo "$tag" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g;s/^-//;s/-$//')
  [ -f "content/tags/$slug/_index.md" ] || echo "missing: $tag -> content/tags/$slug/_index.md"
done < tmp/tag-values.txt
```

- [ ] **Step 4: Verify all descriptions start with "Street art photos tagged"**

Run:

```bash
bad=0
for f in $(find content/tags -mindepth 2 -name '_index.md'); do
  desc=$(grep '^description:' "$f" | sed 's/^description: *"//;s/"$//')
  case "$desc" in
    "Street art photos tagged "*) ;;
    *) echo "bad prefix: $f -- $desc"; bad=$((bad+1));;
  esac
done
echo "bad=$bad"
```

Expected: `bad=0`.

- [ ] **Step 5: Verify ceiling**

Run:

```bash
for f in $(find content/tags -mindepth 2 -name '_index.md'); do
  desc=$(grep '^description:' "$f" | sed 's/^description: *"//;s/"$//')
  [ ${#desc} -gt 160 ] && echo "desc >160 ($((${#desc}))): $f"
done
```

Expected: no output.

- [ ] **Step 6: Build and verify the description renders on a tag page**

Run:

```bash
make build 2>&1 | tail -3
grep -o '<meta name=description content="[^"]*"' public/tags/birds/index.html
```

Expected: build succeeds; the description meta tag on `/tags/birds/` is the one just written.

- [ ] **Step 7: Commit**

Run:

```bash
git add content/tags/
git commit -m "content(taxonomy): write descriptions for tag term pages"
```

## Task 4: Write descriptions for city, country, artist, year term pages (~50 files)

**Files:**
- Create: one `_index.md` per term across these four axes

**Shape** (verbatim from spec):

| Axis | Prefix |
|---|---|
| City | "Street art photos from `<city>`" |
| Country | "Street art photos from `<country>`" |
| Artist | "Street art photos by `<artist>`" |
| Year | "Street art photos from `<year>`" |

Optionally followed by an em-dash and grounded flavour, same rules as Task 3.

**Length:** 80–140 chars target, 160 ceiling.

- [ ] **Step 1: Build the lists for each axis**

Run:

```bash
for axis_field in cities countries artists years; do
  grep -h "^$axis_field:" content/posts/*.md \
    | sed "s/^$axis_field: \[//;s/\]$//" \
    | tr ',' '\n' | sed 's/^ *//;s/ *$//' \
    | grep -v '^$' | sort -u > tmp/$axis_field-values.txt
  echo "$axis_field: $(wc -l < tmp/$axis_field-values.txt) distinct values"
done
```

Expected counts: ~20 cities, ~7 countries, ~14 artists, ~9 years.

- [ ] **Step 2: Create `_index.md` for each city**

For each city in `tmp/cities-values.txt`:

1. Compute Hugo's slug (lowercase, non-alnum → `-`).
2. Identify the posts in that city and read their alts/tags for grounded flavour.
3. Compose the description.
4. Write `content/cities/<slug>/_index.md`:

```yaml
---
title: "<City>"
description: "Street art photos from <City>..."
---
```

Example for `content/cities/liverpool/_index.md`:

```yaml
---
title: "Liverpool"
description: "Street art photos from Liverpool — the Baltic Triangle, Beatles murals, and Liverpool FC tributes."
---
```

The flavour clause is citable: posts with `cities: [Liverpool]` carry tags `Baltic Triangle`, `Beatles`, and `Liverpool FC`.

- [ ] **Step 3: Repeat for countries, artists, years**

Identical procedure with the appropriate prefix:
- `content/countries/<slug>/_index.md` — "Street art photos from `<country>`."
- `content/artists/<slug>/_index.md` — "Street art photos by `<artist>`."
- `content/years/<year>/_index.md` — "Street art photos from `<year>`."

Year terms don't need slugification (just the digit string).

For artist or country terms with only one or two posts, the bare prefix is acceptable.

- [ ] **Step 4: Verify counts and ceilings**

Run:

```bash
for axis_field in cities countries artists years; do
  axis_singular=$(echo "$axis_field" | sed 's/ies$/y/;s/s$//')
  values=$(wc -l < tmp/$axis_field-values.txt)
  files=$(find content/$axis_field -mindepth 2 -name '_index.md' 2>/dev/null | wc -l)
  echo "$axis_field: $values values, $files _index.md files"
done

# Ceiling check
for f in $(find content/cities content/countries content/artists content/years -mindepth 2 -name '_index.md' 2>/dev/null); do
  desc=$(grep '^description:' "$f" | sed 's/^description: *"//;s/"$//')
  [ ${#desc} -gt 160 ] && echo "desc >160 ($((${#desc}))): $f"
done
```

Expected: each axis's file count equals its value count; no length violations.

- [ ] **Step 5: Build and spot-check**

Run:

```bash
make build 2>&1 | tail -3
grep -o '<meta name=description content="[^"]*"' public/cities/liverpool/index.html public/artists/banksy/index.html 2>/dev/null
```

Expected: build succeeds; descriptions render correctly on the sampled term pages.

- [ ] **Step 6: Commit**

Run:

```bash
git add content/cities/ content/countries/ content/artists/ content/years/
git commit -m "content(taxonomy): describe city, country, artist, year term pages"
```

## Task 5: Write descriptions for taxonomy index pages and section/special pages

**Files:**
- Create or modify: `content/tags/_index.md`, `content/cities/_index.md`, `content/countries/_index.md`, `content/artists/_index.md`, `content/years/_index.md`
- Modify: `content/tags/by-count.md` (already exists)
- Modify: `content/_index.md` (home; already exists)
- Modify: `content/posts/_index.md` (already exists)
- Modify: `content/colophon.md` (already exists; description only if body exists)
- Modify or create: `content/404.md` (404 page content)

**Shape** (verbatim from spec):

| Page | Description |
|---|---|
| `/tags/` | "Browse street art photos by the subjects, themes, people, and styles they depict." |
| `/tags/by-count/` | "Street art photo tags ordered by how often they appear." |
| `/cities/` | "Browse street art photos by city." |
| `/countries/` | "Browse street art photos by country." |
| `/artists/` | "Browse street art photos by named artist." |
| `/years/` | "Browse street art photos by year taken." |
| `/` (home) | One- to two-sentence summary of what the site is — citable to existing site tagline and content scope. |
| `/posts/` | "All street art photos, newest first." |
| `/colophon/` | Skip if body is still a stub. If body exists, summarise the colophon. |
| `/404/` | "This page does not exist. Try the homepage or browse by tag." |

**Length:** 80–140 chars target, 160 ceiling.

- [ ] **Step 1: Create or modify each `_index.md` / content file**

For each surface in the table:

1. If the file already exists, use `Edit` to add or update the `description:` line in front matter. Don't touch other fields.
2. If the file doesn't exist (e.g. `content/tags/_index.md`), create it:

```yaml
---
title: "Tags"
description: "Browse street art photos by the subjects, themes, people, and styles they depict."
---
```

- [ ] **Step 2: Verify each surface has a description**

Run:

```bash
for f in content/_index.md content/posts/_index.md content/tags/_index.md content/cities/_index.md content/countries/_index.md content/artists/_index.md content/years/_index.md content/tags/by-count.md content/colophon.md content/404.md; do
  if [ -f "$f" ]; then
    has=$(grep -c '^description:' "$f")
    echo "$f: description=$has"
  else
    echo "$f: missing file"
  fi
done
```

Expected: every file listed exists and has `description=1` (except colophon if explicitly skipped).

- [ ] **Step 3: Build and spot-check**

Run:

```bash
make build 2>&1 | tail -3
grep -o '<meta name=description content="[^"]*"' public/index.html public/posts/index.html public/tags/index.html public/cities/index.html 2>/dev/null
```

Expected: build succeeds; each index has its specific description.

- [ ] **Step 4: Run the full check**

Run:

```bash
make check 2>&1 | grep -E '→|ok|valid|WARNING|INVALID|MISSING|issues found' | head -25
```

Expected: pa11y clean on homepage and a post page, htmltest no new errors, RSS feed valid.

- [ ] **Step 5: Final cross-page sanity sweep**

Confirm no page emits the site-default description anymore:

```bash
default_desc=$(grep '^description' hugo.toml | head -1 | sed 's/.*= *"//;s/"$//')
# This is rough; tolerate some edge pages (404, etc.)
grep -rL "$default_desc" public/ --include='index.html' 2>/dev/null | wc -l
echo "Pages NOT using the site-default description"
```

Expected: a large number (most pages now have their own description).

- [ ] **Step 6: Commit**

Run:

```bash
git add content/
git commit -m "content(config): describe index, section, and special pages"
```

## Wrap-up

After Task 5 commits, the chain of 5 commits is:

1. `feat(post): support headline and sr-only title h2 fallback` (template)
2. `content(post): write titles and descriptions for all photo posts` (109 posts)
3. `content(taxonomy): write descriptions for tag term pages` (~99 files)
4. `content(taxonomy): describe city, country, artist, year term pages` (~50 files)
5. `content(config): describe index, section, and special pages` (~10 files)

At this point every page emits a unique title and description in `<head>`, OG, Twitter, RSS, and the post page has either a visible `headline` or an SR-only `title` heading.

If any single task's commit becomes too large to review, the implementer may split it by sub-axis (e.g. cities separately from artists in Task 4) — but the editorial-voice consistency benefits from doing each axis in one focused pass per subagent.
