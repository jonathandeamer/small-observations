# Tags Index Sort Switcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second sort order to the `/tags/` index page — `/tags/by-count/` renders the same data by post count, descending — with a one-line switch link on each page that links to the other.

**Architecture:** Override `terms.html` only for the tags taxonomy (Hugo uses the singular `tag/` directory for taxonomy templates). Add a stub content file at `content/tags/by-count.md` whose `layout` front-matter points at a new `layouts/tags/by-count.html` (Hugo uses the plural `tags/` directory for regular pages inside the tags section). Both templates render the same shape; they differ only in the sort source and which side of the switcher is active. A small `.terms-sort` CSS rule styles the switcher. All other taxonomy indexes continue to use the unchanged `_default/terms.html`.

**Tech Stack:** Hugo 0.161.1, hand-written HTML templates, hand-written CSS, no JavaScript.

> ⚠️ **Hugo template-lookup wart, locked in by the spec:**
> - For the taxonomy index page (`/tags/`): Hugo looks up `layouts/tag/terms.html` — **singular** directory.
> - For a regular page inside the tags section (`/tags/by-count/`): Hugo looks up `layouts/tags/by-count.html` — **plural** directory.
> The directory name differs between the two files. This is by Hugo's design.

---

## Task 1: Create the alphabetical `terms.html` override for tags

**Files:**
- Create: `themes/notebook/layouts/tag/terms.html`

- [ ] **Step 1: Create the file**

```html
{{ define "title" }}{{ .Title }} · {{ site.Title }}{{ end }}

{{ define "main" }}
<section class="list-page terms-page">
  <header class="section-head">
    <h2>{{ .Title }}</h2>
    <span class="rule"></span>
    <span class="glyph">✦</span>
  </header>

  <p class="terms-sort smallcaps">
    <span class="terms-sort-active">A&ndash;Z</span>
    <span class="terms-sort-sep">·</span>
    <a href="{{ "/tags/by-count/" | relURL }}">view by count</a>
  </p>

  <ul class="terms">
    {{ range .Data.Terms.Alphabetical }}
      <li>
        <a href="{{ .Page.RelPermalink }}">
          <span class="term-name">{{ .Page.Title }}</span>
          <span class="term-count smallcaps">{{ .Count }}</span>
        </a>
      </li>
    {{ end }}
  </ul>
</section>
{{ end }}
```

This is structurally identical to `themes/notebook/layouts/_default/terms.html` plus the `<p class="terms-sort">` block before the list. The `{{ define "main" }}` is unchanged in shape so the override slots into the existing `baseof.html` cleanly.

- [ ] **Step 2: Verify the file exists**

Run:

```bash
ls -la themes/notebook/layouts/tag/terms.html
```

Expected: file exists, non-zero size.

## Task 2: Create the by-count content stub

**Files:**
- Create: `content/tags/by-count.md`

Hugo only auto-generates `/tags/<term>/` URLs for tags that exist in front matter. Since no post is tagged `by-count` (and per the spec, none ever will be), `/tags/by-count/` is free for a regular content page. The content file is just metadata; the body is empty.

- [ ] **Step 1: Create the file**

```markdown
---
title: "Tags"
layout: "by-count"
---
```

The `title` is `Tags` (not `Tags by count`) so the `<h2>` on the page reads the same as `/tags/`. The page-vs-page distinction is communicated by the switcher line, not by the heading.

- [ ] **Step 2: Verify the file exists**

Run:

```bash
ls -la content/tags/by-count.md && cat content/tags/by-count.md
```

Expected: file exists; front matter prints as shown above.

## Task 3: Create the by-count layout

**Files:**
- Create: `themes/notebook/layouts/tags/by-count.html`

Note the directory: `layouts/tags/` (plural), not `layouts/tag/` (singular). This is because the file is a layout for a regular page within the `tags` section, not for the taxonomy index. See the wart note at the top of this plan.

- [ ] **Step 1: Create the file**

```html
{{ define "title" }}{{ .Title }} · {{ site.Title }}{{ end }}

{{ define "main" }}
<section class="list-page terms-page">
  <header class="section-head">
    <h2>{{ .Title }}</h2>
    <span class="rule"></span>
    <span class="glyph">✦</span>
  </header>

  <p class="terms-sort smallcaps">
    <a href="{{ "/tags/" | relURL }}">view alphabetically</a>
    <span class="terms-sort-sep">·</span>
    <span class="terms-sort-active">by count</span>
  </p>

  <ul class="terms">
    {{ range site.Taxonomies.tags.ByCount }}
      <li>
        <a href="{{ .Page.RelPermalink }}">
          <span class="term-name">{{ .Page.Title }}</span>
          <span class="term-count smallcaps">{{ .Count }}</span>
        </a>
      </li>
    {{ end }}
  </ul>
</section>
{{ end }}
```

`site.Taxonomies.tags.ByCount` returns the term list sorted by post count descending. Hugo's secondary sort within equal counts is by term name alphabetically — which matches the spec's tie-break.

- [ ] **Step 2: Verify the file exists**

Run:

```bash
ls -la themes/notebook/layouts/tags/by-count.html
```

Expected: file exists, non-zero size.

## Task 4: Add CSS for the switcher

**Files:**
- Modify: `themes/notebook/assets/css/site.css` (add a new block near the existing `.terms` rules around line 193)

- [ ] **Step 1: Add the switcher styles**

Use `Edit` with `old_string` set to the exact existing block:

```css
.terms { list-style: none; padding: 0; margin: 0; max-width: var(--measure); border-top: 1px solid var(--rule); }
.terms li { border-bottom: 1px solid var(--rule); }
.terms a { display: flex; justify-content: space-between; align-items: baseline; padding: 0.7rem 0.25rem; color: var(--ink); text-decoration: none; }
.terms a:hover { color: var(--coral); }
.terms .term-name { font-size: 1.1rem; }
.terms .term-count { color: var(--muted); font-size: 0.85rem; }
```

and `new_string` set to the same block with the switcher rules appended:

```css
.terms { list-style: none; padding: 0; margin: 0; max-width: var(--measure); border-top: 1px solid var(--rule); }
.terms li { border-bottom: 1px solid var(--rule); }
.terms a { display: flex; justify-content: space-between; align-items: baseline; padding: 0.7rem 0.25rem; color: var(--ink); text-decoration: none; }
.terms a:hover { color: var(--coral); }
.terms .term-name { font-size: 1.1rem; }
.terms .term-count { color: var(--muted); font-size: 0.85rem; }

.terms-sort { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0 0 0.5rem; color: var(--muted); font-size: 0.82rem; }
.terms-sort a { color: var(--link); text-decoration: none; border-bottom: 1px solid var(--rule); padding-bottom: 1px; }
.terms-sort a:hover { color: var(--coral); border-color: var(--coral); }
.terms-sort-active { color: var(--muted); }
.terms-sort-sep { color: var(--coral); }
```

Notes on the choices:
- `flex-wrap: wrap` is the defensive insurance from the spec — at 320px wide the line is well under one line, but this protects against future longer copy.
- `gap: 0.5rem` gives breathing room between the three pieces (active label, separator dot, link).
- `font-size: 0.82rem` matches the existing `.taxonomy-count` size for visual consistency.
- The coral interpunct (`·`) echoes the masthead's coral middot.
- Link styling matches the existing `.post-meta a` pattern (border-bottom rule, hovers to coral).

- [ ] **Step 2: Verify the addition**

Run:

```bash
grep -c '^.terms-sort' themes/notebook/assets/css/site.css
```

Expected: `5` (one for each of `.terms-sort`, `.terms-sort a`, `.terms-sort a:hover`, `.terms-sort-active`, `.terms-sort-sep`).

## Task 5: Document the reserved tag name in CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (the existing `## Tag taxonomy` section)

- [ ] **Step 1: Append a reserved-tag note to the Tag taxonomy section**

Find the line in `CLAUDE.md` that ends the existing `## Tag taxonomy` section:

```
See `docs/superpowers/specs/2026-05-17-tag-taxonomy-design.md` for the full design and rationale.
```

Use `Edit` to insert a new reserved-tag bullet immediately above that line:

- `old_string`:

```
See `docs/superpowers/specs/2026-05-17-tag-taxonomy-design.md` for the full design and rationale.
```

- `new_string`:

```
**Reserved tag names.** `by-count` must never be used as a tag value. The URL `/tags/by-count/` is claimed by the by-count sort variant of the tags index page (see `docs/superpowers/specs/2026-05-17-tags-index-sort-design.md`). Using `by-count` as a tag would collide.

See `docs/superpowers/specs/2026-05-17-tag-taxonomy-design.md` for the full design and rationale.
```

- [ ] **Step 2: Verify the insertion**

Run:

```bash
grep -n "Reserved tag names" CLAUDE.md
```

Expected: one match in the Tag taxonomy section.

## Task 6: Build, verify both URLs, verify sibling taxonomies are untouched, commit

**Files:**
- Read: `public/tags/index.html`, `public/tags/by-count/index.html`, `public/cities/index.html`

- [ ] **Step 1: Build the site**

Run:

```bash
make build 2>&1 | tail -10
```

Expected: build succeeds. Page count should increase by exactly 1 vs the previous build (296 → 297) because we've added the `/tags/by-count/` page.

If the build fails because of a template lookup error, double-check the directory split: `terms.html` is in `themes/notebook/layouts/tag/` (singular), `by-count.html` is in `themes/notebook/layouts/tags/` (plural). Mixing them up is the most likely failure mode.

- [ ] **Step 2: Verify `/tags/` renders the alphabetical view with the switcher**

Run:

```bash
test -f public/tags/index.html && echo "exists"
grep -c 'terms-sort' public/tags/index.html
grep -o '<a [^>]*href="[^"]*by-count[^"]*"' public/tags/index.html
```

Expected: `exists`; at least 1 match for `terms-sort`; the link to `/tags/by-count/` is present.

- [ ] **Step 3: Verify `/tags/by-count/` renders the by-count view**

Run:

```bash
test -f public/tags/by-count/index.html && echo "exists"
grep -c 'terms-sort' public/tags/by-count/index.html
grep -o '<a [^>]*href="[^"]*/tags/"' public/tags/by-count/index.html | head -1
```

Expected: `exists`; at least 1 match for `terms-sort`; the link back to `/tags/` is present.

- [ ] **Step 4: Spot-check that by-count ordering is descending**

Run:

```bash
grep -oE 'term-count[^>]*>[0-9]+' public/tags/by-count/index.html | grep -oE '[0-9]+' | head -10
```

Expected: a descending sequence (the top 10 tags by count). The first value should be at least `39` (the `animal` tag count from `c037fc4`).

Then compare to the alphabetical page:

```bash
grep -oE 'term-count[^>]*>[0-9]+' public/tags/index.html | grep -oE '[0-9]+' | head -10
```

Expected: a *not-necessarily-descending* sequence — counts in alphabetical-by-name order. Different from the by-count list.

- [ ] **Step 5: Verify sibling taxonomies still use the default template (no accidental override)**

Run:

```bash
test -f public/cities/index.html && grep -c 'terms-sort' public/cities/index.html
```

Expected: file exists; `0` matches for `terms-sort` (cities should NOT have the switcher).

Same for the others:

```bash
for t in countries artists years; do
  echo "$t:"
  test -f "public/$t/index.html" && grep -c 'terms-sort' "public/$t/index.html"
done
```

Expected: each file exists; `0` matches per file.

- [ ] **Step 6: Run `make check` for link health**

Run:

```bash
make check 2>&1 | grep -E '→|ok|valid|WARNING|INVALID|MISSING|issues found' | head -20
```

Expected: no new `htmltest` errors, no pa11y issues introduced, sitemap and RSS still validate.

- [ ] **Step 7: Commit**

Run:

```bash
git add themes/notebook/layouts/tag/terms.html themes/notebook/layouts/tags/by-count.html content/tags/by-count.md themes/notebook/assets/css/site.css CLAUDE.md
git diff --cached --name-only
git commit -m "feat(taxonomy): add by-count sort variant to /tags/ index"
```

Expected: commit succeeds; staged file list shows exactly the five files above.

Subject is 56 characters — within the 72-character hook limit.
