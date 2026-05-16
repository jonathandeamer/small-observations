# Pagination Design

**Date:** 2026-05-16
**Status:** Approved

## Goal

Replace Hugo's built-in pagination template with a minimal custom partial that renders `← older · page 2 of 6 · newer →` — text-based, no numbered page links.

## Scope

Only `list.html` currently paginates (`/posts/`). Taxonomy term pages do not paginate and are not affected.

## Changes

### 1. New partial: `pagination.html`

Create `themes/notebook/layouts/partials/pagination.html`. It:

- Receives the page as context (`.`)
- Reads `.Paginator` for current page number, total pages, and prev/next URLs
- Renders nothing when `.Paginator.TotalPages` is 1 (no pagination needed)
- Renders `← older · page N of M · newer →` when there are multiple pages
- `← newer` is an `<a>` link to `.Paginator.Prev.URL` when a previous page exists; a `<span class="pagination-disabled">` when on page 1
- `older →` is an `<a>` link to `.Paginator.Next.URL` when a next page exists; a `<span class="pagination-disabled">` when on the last page
- `page N of M` is a plain `<span class="pagination-info">` in muted colour
- `·` separators are rendered as plain text between the three elements
- Wrapped in `<nav class="pagination" aria-label="Page navigation">`

### 2. `list.html`

Replace:
```html
{{ template "_internal/pagination.html" . }}
```
with:
```html
{{ partial "pagination.html" . }}
```

### 3. CSS additions to `site.css`

Add a pagination block:

```css
/* pagination */
.pagination { display: flex; justify-content: center; align-items: baseline; gap: 1rem; margin: 2rem 0 1rem; font-size: 0.88rem; }
.pagination a { color: var(--link); text-decoration: none; border-bottom: 1px solid var(--link); padding-bottom: 1px; }
.pagination-disabled { color: var(--muted); }
.pagination-info { color: var(--muted); }
```

## Invariants

- The built-in `_internal/pagination.html` is not used anywhere after this change
- Single-page lists render no pagination element at all
- No numbered page links appear anywhere in the output
- Accessible: `<nav>` with `aria-label`, disabled states use `<span>` (not links with `aria-disabled`)
