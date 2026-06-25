# Related-posts strip — design

**Date:** 2026-06-25
**Status:** Approved, pending implementation
**Branch:** `feat/related-posts`

## Goal

Add a "Related" strip to the foot of each single post page, surfacing up to
three other posts that share an artist, tag, or city with the current post.
The site has no JavaScript and no third-party requests; this feature must
stay within that constraint (static HTML + CSS only, built at `hugo` time).

This gives readers who land deep from search or a shared link a way to keep
browsing without climbing back up to the archive indexes — a natural fit for
a photo archive where posts cluster by artist, subject, and place.

## Why Hugo's `[related]` engine

Hugo ships a built-in keyword-similarity engine (`site.RegularPages.Related`).
It ranks candidate pages by weighted overlap across configured indices and
degrades gracefully when there's no perfect match — a post with a partial
artist/tag overlap still surfaces. This beats a hand-rolled "same artist" or
"same city" filter, both of which go empty or noisy on this archive (many
posts have no artist; cities like London are huge).

## Configuration

Added to `hugo.toml`:

```toml
[related]
  threshold = 80
  includeNewer = true
  toLower = false
  [[related.indices]]
    name = "artists"
    weight = 90
  [[related.indices]]
    name = "tags"
    weight = 70
  [[related.indices]]
    name = "cities"
    weight = 40
```

Rationale, decisions captured so they aren't re-litigated later:

- **Weights `artists 90 > tags 70 > cities 40`.** This reflects how posts in
  this archive actually relate: same artist is the strongest cue, then shared
  subject/theme via tags, then geography. City is weighted lowest because a
  shared large city (London) is weak signal on its own.
- **`threshold = 80`** keeps matches meaningful rather than padding the strip
  with tenuous links. Combined with "hide when empty" (below), a post with no
  real relations shows no strip at all.
- **`includeNewer = true`.** Without this, a post can only relate to posts
  older than itself, so newer posts never surface as related on older posts.
  For a browsable archive (not a time-ordered blog feed) we want relations to
  work in both directions.
- **`toLower = false`.** Tags and artists are mixed-case by design
  (`John Lennon`, `Liverpool FC`); index names must match the taxonomy names
  exactly. A comment in `hugo.toml` notes this so it isn't "tidied" later.
- No `keywords` aliasing is needed: `artists`, `tags`, and `cities` are real
  taxonomies / front-matter params, which the engine indexes by name directly.

## Component: `layouts/partials/related.html`

A new partial, called with the current page as context.

Behaviour:

1. Compute `$related := first 3 (site.RegularPages.Related $page)`.
   - `site.RegularPages` (not `.Site.Pages`) so only real, **published** posts
     are candidates — this respects the existing `publishDate` gating that
     keeps unpublished posts out of production builds, identical to the home
     gallery and archives.
2. **If `$related` is empty → render nothing.** No heading, no wrapper, no
   whitespace. The strip is omitted entirely; the page foot is unchanged for
   posts with no relations.
3. Otherwise render:

   ```html
   <aside class="related" aria-label="Related posts">
     <h2 class="related-head">Related</h2>
     <div class="gallery related-grid">
       {{ range $related }}
         {{ partial "gallery-card.html" (dict "page" . "eager" false) }}
       {{ end }}
     </div>
   </aside>
   ```

   - Reuses the existing `gallery-card.html` partial verbatim, so the
     200/400 WebP+JPEG pipeline, `srcset`/`sizes`, and the date·place caption
     are identical to the homepage grid. No new image logic.
   - **All cards lazy (`eager=false`).** The LCP image is the post photo at
     the top of the page; nothing in the related strip should compete for
     `fetchpriority`. This preserves the LCP invariant noted in CLAUDE.md.

## Placement

In `themes/notebook/layouts/_default/single.html`, the partial is invoked
between the post-meta block and the colophon:

```
  {{ partial "post-meta.html" . }}

  {{ partial "related.html" . }}

  <p class="post-colophon"> … </p>
```

So the reading order is: photo → title → body → meta → **related** → colophon
("← all posts"). The related strip sits after the post's own metadata and
before the link back to the full archive — a reader finishes the post, sees a
few related observations, then the escape hatch to everything.

## Styling

In `themes/notebook/assets/css/site.css`:

- Reuse the existing `.gallery` grid rules for `.related-grid` so card layout,
  gaps, and responsive `sizes` behaviour match the homepage with no
  duplication. Add only what's specific to the strip:
  - Top separation from the meta above (a hairline rule / top border and
    margin), consistent with the existing visual rhythm of the page foot.
  - `.related-head` heading spacing. Match the existing section-heading
    treatment (the coral `✦` glyph style used elsewhere) if it sits cleanly;
    otherwise a lighter standalone heading style in keeping with the page.
- The strip should read as a quiet footer block, not compete with the post
  photo. Up to three cards = at most one short row.

## Accessibility & standards

- `<aside aria-label="Related posts">` — a labelled complementary landmark,
  appropriate for tangentially-related navigation.
- `<h2>` keeps heading hierarchy valid: the single `<h1>` remains the post
  title (untouched). On posts with no headline the `<h1>` is `sr-only`, but it
  still exists, so the `<h2>` is correctly nested.
- Cards are real `<a>` links (via the existing partial) — keyboard-navigable,
  no JS, no state.
- Must clear `make check`: pa11y (homepage + a random post), htmltest
  (internal links, alt text), vnu (W3C HTML validation on homepage + one post).

## Verification

- `make build` then `make check`.
- Manual `make dev` + browser on:
  - a post with known artist+tag overlap → strip shows up to 3 sensible cards;
  - a post with no relations (e.g. minimal tags, no artist, unique city) →
    strip is absent entirely.
- Confirm the post photo still wins LCP (related cards are lazy, not eager).

## Out of scope (YAGNI)

- No "top up with recent posts" padding — an honest empty strip is preferred
  to filler. (Considered and rejected during design.)
- No separate related-thumbnail compression profile — reuse the gallery card
  pipeline as-is.
- No related strips on taxonomy/term/list pages — single post pages only.
- No config UI or per-post override of the related set.
