# Gallery Layout for Taxonomy and List Pages

**Date:** 2026-05-16
**Status:** Approved

## Goal

Replace the horizontal card layout on taxonomy term pages and the `/posts/` list with a square photo grid matching the homepage favourites gallery. All these pages should sort by date taken (ascending from oldest), reversed — i.e. most recent first.

## Scope

| Template | Change |
|---|---|
| `taxonomy.html` | Switch to gallery grid; ordering already correct |
| `list.html` | Switch to gallery grid; fix sort order to date taken |
| `index.html` | Use new shared partial; no visual change |
| `terms.html` | No change — lists tags/cities/etc alphabetically, no images |

## Changes

### 1. New partial: `gallery-card.html`

Extract the fav-card markup currently inline in `index.html` into `themes/notebook/layouts/partials/gallery-card.html`. Takes a page as context. Renders:

- A linked square image (400px, WebP + JPEG fallback via `<picture>`)
- Date (taken) + place metadata below the image
- Same markup and behaviour as the current homepage fav-card

### 2. CSS: rename `.favourites-grid` → `.gallery-grid`

The grid class is now a shared pattern used across the site, not specific to the homepage. Rename in `site.css` and update all references in templates. No change to the grid behaviour (4 columns, clamp gap, 2-column at narrow viewports).

### 3. `index.html`

Replace inline fav-card markup with `{{ partial "gallery-card.html" . }}` inside the existing `favourites-grid` (now `gallery-grid`) loop. No visual change.

### 4. `taxonomy.html`

- Replace `.cards` container and `post-card.html` loop with `.gallery-grid` and `gallery-card.html`
- Keep existing `.ByDate.Reverse` ordering (date taken, most recent first)
- Keep section header and photo count

### 5. `list.html`

- Replace `.cards` container and `post-card.html` loop with `.gallery-grid` and `gallery-card.html`
- Change sort from `.ByPublishDate.Reverse` to `.ByDate.Reverse`
- Keep existing pagination

### 6. Delete `post-card.html`

After the above changes `post-card.html` is unused. Delete it and its associated CSS (`.card`, `.card-thumb`, `.card-meta`, `.card-date`, `.card-place`, `.card-title`, `.cards`).

## Invariants

- The homepage favourites section remains curated (weighted, first 8 only) — this change does not affect that logic
- Pagination on `/posts/` is preserved
- `terms.html` (index pages like `/tags/`, `/cities/`) is not touched
