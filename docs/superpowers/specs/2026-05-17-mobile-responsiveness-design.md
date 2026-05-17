# Mobile Responsiveness Design

## Context

The site is already broadly responsive: it has a viewport meta tag, fluid page padding, clamp-based typography, responsive images, and a gallery breakpoint that changes four columns to two below 640px.

The remaining issue is not that the site is unusable on phones. The issue is that several dense areas still keep their desktop structure at narrow widths, which can make the site feel cramped on small phones and less polished on tablets.

This pass should preserve the current small-web character: one stylesheet, no JavaScript, no new assets, no framework, and no separate mobile identity.

## Goals

- Improve reading comfort on post pages.
- Improve browsing comfort on the homepage, galleries, taxonomy pages, and list pages.
- Support very small phones around 320px, modern phones around 390px, the existing 640px gallery breakpoint, and small tablets around 768-900px.
- Keep desktop layout and visual language substantially unchanged.
- Keep the work in `themes/notebook/assets/css/site.css` unless a template issue is discovered during implementation.

## Non-Goals

- Do not redesign the site.
- Do not add JavaScript.
- Do not introduce a new build tool, CSS framework, or second stylesheet.
- Do not change content, taxonomy behaviour, image generation, or front matter.
- Do not make mobile look like a separate product.

## Approach

Use a small set of targeted responsive CSS rules rather than a broad rewrite.

Recommended responsive bands:

- `max-width: 760px`: reduce medium-screen and small-tablet crowding.
- `max-width: 640px`: refine the existing phone gallery breakpoint.
- `max-width: 380px`: protect very small phones from compressed labels, counts, and metadata.

These breakpoints are intentionally few. They should act as guardrails for dense components, not as a complete alternative layout system.

## Component Behaviour

### Page Shell And Masthead

The existing fluid `.page` padding and masthead type scale should remain. If viewport testing shows the smallest phones feel crowded, reduce only the horizontal padding and masthead bottom spacing inside the narrowest breakpoint.

Do not change the font, colour palette, masthead wording, or overall page width.

### Post Pages

Post pages should remain photo-centred and text-light.

`.post-meta` is the most likely narrow-screen issue because it uses `grid-template-columns: max-content 1fr`. On phone widths, it should switch to a one-column or compact stacked layout so labels and values do not fight for space.

Acceptable mobile shape:

- metadata label above or immediately before value
- smaller row gaps than desktop
- no horizontal scrolling
- no clipped city, country, artist, or tag values

Post photos should keep using the existing `photo.html` responsive image pipeline. The CSS can adjust margins if needed, but the image processing and `srcset` logic should not change.

### Browse Menu

The homepage browse rows currently use `grid-template-columns: 2.5rem 1fr auto`. This is fine on desktop but can crowd labels and counts on narrow screens.

On smaller widths, the row should keep the same information but allow more natural wrapping. The number can remain left-aligned, while the count should not force the main label into an awkward narrow column.

Acceptable mobile shapes:

- keep number, label, and count visible
- allow the count to sit under or close to the label on very narrow screens
- keep row tap targets comfortable
- preserve the restrained list-like feel

### Gallery Grid

The existing gallery grid already changes from four columns to two below 640px. Keep that behaviour as the baseline.

Improve the surrounding details rather than inventing a new gallery:

- tune gaps for phone widths
- ensure gallery metadata does not collide or feel oversized
- consider a three-column tablet band only if viewport testing shows four columns are too tight before 640px

The gallery should remain visually recognisable as the current gallery.

### Terms, Lists, And Pagination

Terms and pagination should remain simple text-first controls.

On very small phones:

- terms rows should avoid forcing long names and counts onto a cramped single line
- pagination should wrap or stack cleanly
- list introductions should retain readable measure and spacing

Do not add icons or new navigation components.

## Verification

Run:

```bash
make build
```

Then manually inspect representative pages at these viewport widths:

- 320px
- 390px
- 640px
- 768-900px

Representative pages:

- homepage
- one post page with metadata
- `/posts/`
- a taxonomy term page with a gallery
- a terms index page such as `/tags/` or `/countries/`

Check for:

- no horizontal scrolling
- no clipped text
- browse rows remain readable and tappable
- post metadata reads naturally
- galleries retain stable square thumbnails
- desktop layout is not meaningfully changed

## Open Questions

None. The chosen direction is subtle mobile refinement across phones and small tablets.
