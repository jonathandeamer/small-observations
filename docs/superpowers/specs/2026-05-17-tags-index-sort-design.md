# Tags Index Sort Switcher Design

## Context

`/tags/` is now the largest taxonomy index on the site at 129 distinct entries. The current `themes/notebook/layouts/_default/terms.html` template renders alphabetically by `.Data.Terms.Alphabetical` and serves all five taxonomies (`tags`, `cities`, `countries`, `artists`, `years`). For 130-odd tags, alphabetical alone makes the most-used categories hard to find — a visitor who wants to know which subjects recur most has to scan the whole list and check counts mentally.

Adding a second sort order (by post count, descending) gives visitors a second path into the archive. Other taxonomies are small enough that alphabetical is fine; this design changes only the tags index.

## Goal

Offer two pre-built sort orders for `/tags/`:

- **Alphabetical** at `/tags/` (default; current behaviour preserved).
- **By count, descending** at `/tags/by-count/`.

Each page links to the other via a small switcher in the section header. No JavaScript. Each URL is a static, deep-linkable, statically-served page.

## Design decisions

### URLs

- **`/tags/`** — alphabetical (default).
- **`/tags/by-count/`** — by-count, descending. Ties within the same count are broken alphabetically.

Hierarchical nesting under `/tags/` keeps the two views feeling like one feature. `/tags/by-count/` would normally collide with a tag named `by-count`, but Hugo only generates term pages for tags that exist in front matter — so the URL is safe as long as no post is ever tagged `by-count`. This becomes a one-word reserved-tag rule: cheap and easy to remember.

### Switch link

A small one-line element appears between the section header and the terms list. The active sort is plain muted text; the inactive sort is a link.

On `/tags/`:

```
A–Z  ·  view by count
```

On `/tags/by-count/`:

```
view alphabetically  ·  by count
```

Visual register: smallcaps muted text, matching the style of `.taxonomy-count` on individual term pages (`.smallcaps` class, `var(--muted)` colour, ~0.82–0.88rem font size). Alignment to be settled at implementation time — either left (matches the existing `.taxonomy-count` pattern) or right (convention for sort controls). Both work; pick whichever looks calmer in the browser. The interpunct (`·`) separator follows the masthead's typographic vocabulary.

### Scope

Tags only. `/cities/`, `/countries/`, `/artists/`, `/years/` continue to use the shared `_default/terms.html` and stay alphabetical. If sort-switching is later wanted on cities (the second most useful by-count view), the same pattern extends straightforwardly.

### Mobile behaviour

The switcher is a single short string (~19 characters) and inherits the page's existing responsive padding. It needs no dedicated media query.

Defensive insurance: `flex-wrap: wrap` on the switcher container, so if a future change to the copy makes it longer it can break onto two lines instead of overflowing.

Existing mobile rules from commit `f0ba6a7` are unaffected:
- 760px: gallery and browse-menu tweaks. Terms unchanged.
- 640px: gallery to two columns, post-meta stacks. Terms unchanged.
- 380px: `.terms a` flips to vertical flex (name above count). The switcher above the list continues to render as a single line on this width.

### Template structure

Two near-identical templates, deliberately kept separate. Each is ~25 lines. Parameterising one template with `{{ if }}` branches to swap the sort source and the link target would save ~25 lines at the cost of a single template that "knows" about two pages — more fragile, harder to read.

| File | Status | Responsibility |
|---|---|---|
| `themes/notebook/layouts/tag/terms.html` | NEW | Renders `/tags/` alphabetical. Wraps `site.Taxonomies.tags.Alphabetical`. Switcher reads "A–Z · view by count" with "view by count" linking to `/tags/by-count/`. |
| `content/tags/by-count.md` | NEW | Tiny stub content file. Front matter only: `title`, `layout: "by-count"`. Triggers Hugo to generate the `/tags/by-count/` URL. |
| `themes/notebook/layouts/tag/by-count.html` | NEW | Renders `/tags/by-count/` by count descending. Iterates `site.Taxonomies.tags.ByCount`. Switcher reads "view alphabetically · by count" with "view alphabetically" linking to `/tags/`. |
| `themes/notebook/assets/css/site.css` | MODIFY | Add ~6 lines styling `.terms-sort` (the switcher container and its active/inactive labels). |

The shared `_default/terms.html` is left untouched. Other taxonomies continue using it.

### Why a content file plus a layout, rather than two terms.html overrides

Hugo only allows one `terms.html` per taxonomy. To get a second URL using the same source data, we either:

- Make a content page at `content/tags/by-count.md` with a custom layout. Clean, easy to reason about, content-and-template separation honoured.
- Use Hugo's URL output formats. Heavier machinery for this scope.
- Use a custom output format mapped through aliases. Even heavier.

The content-file approach is the smallest viable mechanism.

## Reserved tag names

To preserve the `/tags/by-count/` URL, **no post may use `by-count` as a tag value**. This is a one-name reservation. Add to CLAUDE.md's `Tag taxonomy` section.

## Out of scope

- Other taxonomy indexes (`/cities/`, `/artists/`, `/countries/`, `/years/`) — stay on `_default/terms.html`, alphabetical only.
- Sub-sort on the by-count page (e.g., "by count then by date last used") — descending count with alphabetical tie-break is enough.
- "Top N" curation — full list rendered both ways.
- CSS-only client-side toggle. Pre-built pages are the chosen approach.
- A tag-cloud-style frequency-sized visualisation.

## Validation

After implementation:

- `/tags/` renders alphabetical (same as before) with a "view by count" link in the header area.
- `/tags/by-count/` renders by count descending, ties alphabetical, with a "view alphabetically" link.
- Both links navigate correctly.
- `make build` succeeds.
- `make check` passes (no new htmltest broken-link errors).
- Both URLs render correctly at 1280px, 760px, 640px, and 380px viewport widths (visual check via `make dev` + browser dev tools).
- `/cities/`, `/countries/`, `/artists/`, `/years/` continue to render exactly as before (no accidental override).
- The `by-count` reserved-tag rule is documented in CLAUDE.md.

## Commit scope

One commit. Touches:

- `themes/notebook/layouts/tag/terms.html` (new)
- `themes/notebook/layouts/tag/by-count.html` (new)
- `content/tags/by-count.md` (new)
- `themes/notebook/assets/css/site.css` (small addition)
- `CLAUDE.md` (one-line reserved-tag note appended to the tag taxonomy section)
