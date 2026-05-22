# Homepage Browse Navigation Design

## Context

The homepage currently puts the archive browse list after the masthead and the "A few favourites" gallery. The list is useful, but it reads as a long block below the fold, especially now that the archive has enough taxonomy pages to make navigation matter.

The homepage should still feel photo-led. The masthead and favourite images are the strongest first impression, and the site should not turn into a directory page. The problem is discoverability: visitors should see immediately that the archive can be browsed by latest posts, favourites, tags, cities, years, countries, and artists.

## Goals

- Surface primary archive navigation near the top of the homepage.
- Keep at least some favourite photos visible early on desktop and mobile.
- Replace the long lower browse list with a lighter exploratory surface.
- Treat mobile as a first-class layout constraint.
- Preserve the existing small-web character: static HTML, no JavaScript, one stylesheet, no new assets, no third-party requests.

## Non-Goals

- Do not redesign the masthead.
- Do not reduce or remove the favourites preview.
- Do not add search, filtering, disclosure widgets, accordions, tabs, or JavaScript.
- Do not preview years or artists as exploratory term lists on the homepage.
- Do not change taxonomy URLs, content front matter, or archive sorting.

## Chosen Direction

Add a compact text browse row directly under the masthead, before the "A few favourites" section:

```text
latest · favourites · tags · cities · years · countries · artists
```

This row is the primary archive router. It should feel like a quiet continuation of the masthead area rather than a new page section. It should not have a large "Browse" heading, item numbers, or counts. Counts add width and compete with the goal of keeping the top area shallow.

The current long browse list below favourites should be replaced by a smaller exploratory section focused only on tags and cities. Tags and cities are the two browse axes most likely to tempt exploration from the homepage because they reveal what the archive contains. Years, countries, and artists remain available from the top router but do not get homepage term previews.

## Desktop Behaviour

On wider viewports, the masthead area should remain left-aligned and calm. The browse row can sit below the tagline with modest spacing, using the site's existing smallcaps or muted-link vocabulary.

The row should be visually lighter than section headings and favourite captions. It is navigation, not a hero element.

The first favourites row should still appear above the fold on a typical laptop viewport. The browse row should add only one line plus a small amount of vertical breathing room.

## Mobile Behaviour

Mobile is the main constraint. The top browse row must be allowed to wrap naturally, but it should be designed to take no more than two lines on common phone widths.

Mobile rules:

- no counts in the top browse row
- no numbering
- no separate "Browse" heading above the row
- links must remain large enough to tap comfortably
- wrapping should happen at separators or link boundaries, not inside words
- the "A few favourites" heading and the start of the image grid should remain visible early on common phone viewports

If the labelled row with all seven links feels too wide in implementation, the fallback is still the same row without the "browse:" prefix:

```text
latest · favourites · tags · cities · years · countries · artists
```

Do not hide lower-priority links on mobile. The router should expose the same destinations across viewport sizes.

## Lower Explore Section

After the favourites gallery, add a smaller section that previews only tags and cities:

```text
Explore
tags: animals · music · protest · stencil · birds · football · more tags
cities: London · Liverpool · New York · San Francisco · Toronto · more cities
```

The exact term set should be generated from taxonomy data rather than hand-written content. Use a restrained limit so the section stays short:

- tags: the first six terms from `site.Taxonomies.tags.ByCount`, excluding reserved or purely structural terms if any are introduced later
- cities: the first six terms from `site.Taxonomies.cities.ByCount`
- each row ends with a link to the full index, such as "more tags" and "more cities"

This is a taste of the archive, not a replacement for `/tags/` or `/cities/`.

## Content And Labelling

Use British English for any public-facing labels.

Recommended labels:

- `latest`
- `favourites`
- `tags`
- `cities`
- `years`
- `countries`
- `artists`
- `more tags`
- `more cities`

Avoid title case in the compact browse row unless implementation shows it reads better with the existing typography. The row should feel more like a line of text than a menu bar.

## Implementation Notes

Likely files:

- `themes/notebook/layouts/index.html`
- `themes/notebook/assets/css/site.css`

The implementation should remove or supersede the existing homepage `.browse` list. Keep taxonomy index templates unchanged.

The top router can be a semantic `<nav>` with an accessible label. The lower exploratory section can use simple paragraphs or lists; choose the markup that gives screen readers a clear structure without adding visual bulk.

## Verification

Run:

```bash
make build
```

Then inspect the homepage at:

- 320px wide
- 390px wide
- 640px wide
- 1280px wide

Check:

- no horizontal scrolling
- top browse row wraps cleanly on mobile
- links remain tappable
- no text overlaps or clipped labels
- at least the beginning of the favourites grid appears early on phones
- the first favourites row remains visible above the fold on typical desktop/laptop viewports
- lower explore section stays short and does not become another long list

## Open Questions

None. The approved direction is a compact masthead-adjacent text router plus a short tags-and-cities exploration section below favourites.
