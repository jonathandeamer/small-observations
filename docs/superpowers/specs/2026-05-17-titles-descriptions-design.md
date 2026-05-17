# Page Titles and Descriptions Design

## Context

Every post and taxonomy page on Small Observations currently emits the same `<title>` (`Small Observations`) and the same `<meta description>` (the site tagline). Search-engine snippets, social-share cards, and RSS items cannot distinguish posts. The templates already wire `.Title` → `<title>`/`og:title`/`twitter:title` and `.Description` → `<meta description>`/`og:description`/`twitter:description`/RSS — the gap is the front-matter values, not the rendering.

Alt text, tags, and body text are now considered authoritative across the archive. Those plus the front-matter fields (city, country, year, artists, date) give a complete, citable surface for a writer to draw on without inventing anything.

## Goal

Hand-write three new front-matter values across the substantive pages of the site:

- `title:` — short, distinctive, unique per page. Always populated.
- `headline:` — optional. When set, renders as a visible `<h2>` on the post page. When absent, the existing visual design is preserved.
- `description:` — concise summary of the page. Always populated.

The writes must:

1. Be **citable, claim by claim**, to the post's or page's own data — never to the image itself, never to external knowledge.
2. Match the site's existing observational, modest voice.
3. Make each page genuinely distinct in search results, social shares, RSS, and assistive-tech navigation.

## Scope

Every "substantive" surface gets the treatment. Approximate counts:

| Surface | Count | Title | Description | Headline |
|---|---|---|---|---|
| Photo posts (`content/posts/*.md`) | 109 | yes | yes | optional |
| Tag term pages (`/tags/<term>/`) | ~99 | (from taxonomy term) | yes | n/a |
| City term pages | 20 | (term) | yes | n/a |
| Artist term pages | 14 | (term) | yes | n/a |
| Year term pages | 9 | (term) | yes | n/a |
| Country term pages | 7 | (term) | yes | n/a |
| Taxonomy index pages (`/tags/`, `/cities/`, `/countries/`, `/artists/`, `/years/`, `/tags/by-count/`) | 6 | (existing) | yes | n/a |
| Home (`/`) | 1 | (existing) | yes | n/a |
| Posts list (`/posts/`) | 1 | (existing) | yes | n/a |
| Colophon (`/colophon/`) | 1 | yes (set) | yes | optional |
| 404 (`/404/`) | 1 | (existing) | yes | n/a |

Roughly **270 unique writes** in total. Term pages take their `title` from the taxonomy value (e.g. `/tags/birds/` titled "Birds") and need a `description` only — which lives in a per-term `_index.md` content file under e.g. `content/tags/birds/_index.md`.

## Source discipline

This is the load-bearing rule. The writer draws **only** from the page's own structured and prose data. Every substantive claim must be citable to a field below.

**Permitted sources for a photo post:**

- `alt:` — what the photo shows.
- Body text after `---` — human-written context (provenance, attribution, where the photo was taken, etc.).
- `tags:` — categorical labels.
- `artists:` — named makers.
- `cities:`, `countries:` — geographical context.
- `date:` — year, month.
- `exif.camera` — only if relevant (rarely).

**Permitted sources for a taxonomy term page (e.g. `/tags/birds/`):**

- The term name itself.
- The alt and body text of every post in the term.
- The tags / artists / cities of those posts.

**Permitted sources for a taxonomy index page (e.g. `/tags/`):**

- The taxonomy's name and what it categorises.
- The site's own structural facts (number of terms, broad scope).

**Forbidden:**

- Looking at the image. Alt text is authoritative; the writer does not re-view the photo.
- External knowledge about depicted people, places, movements, or styles beyond what the post's own text already says. ("British musician Amy Winehouse" — no, unless the post's alt or body already mentions she's a British musician.)
- Inferring neighbourhoods or sub-locations from `exif.lat` / `exif.lon`.
- Evaluative or aesthetic framing ("striking", "powerful", "vibrant", "beautiful").
- Editorialising about why the artwork matters, what the artist meant, what the political situation is.
- Inventing specific examples on tag pages. If a tag's description names example posts, each example must genuinely exist in posts carrying that tag.

## Voice

Observational, modest, plain English. British spellings (`colour`, `grey`, `favourite`, `centre`). No marketing voice. No first-person. No metaphors except where the artwork's own text or composition is metaphorical and the description is directly reporting it.

Same register as the alt-text editorial pass: describes; doesn't praise.

## Length targets

| Field | Target | Hard ceiling |
|---|---|---|
| Post `title:` | 35–60 chars | 70 |
| Post `headline:` (when used) | 25–50 chars | 60 |
| Post `description:` | 110–160 chars | 200 |
| Term-page `description:` | 80–140 chars | 160 |
| Index / special-page `description:` | 80–140 chars | 160 |

"Site name suffix" (`· Small Observations`) is appended automatically by the existing template — the title field holds only the unique part.

## Field shapes by page type

### Photo posts

**`title:`** — distinctive subject + location (or attribution). Sentence-cased, no full stop.

Examples (drawn from real alts):
- "Vampire mural, Liverpool"
- "Ringo Starr in Yellow Submarine scenes, Liverpool"
- "Picasso portrait on a corrugated door, Barcelona"
- "Chuck Berry stencil, London"
- "Memorial mural for George Floyd and Breonna Taylor, San Francisco"

**`description:`** — leads with **"Photo of"** prefix, then a single sentence describing the scene and a clause anchoring it (location, year, artist, or context).

Examples:
- "Photo of a purple vampire holding a lit candle in front of a full moon, painted on a brick wall in Liverpool."
- "Photo of a Banksy-style stencil of two officers searching a Basquiat-style crowned figure, behind clear panels on Golden Lane, London."
- "Photo of a memorial mural for George Floyd and Breonna Taylor, with portraits, raised fists, and Black Lives Matter signs, in San Francisco's Clarion Alley."

**`headline:`** — optional, used only when there is a short phrase that *adds something* the photo and alt text don't already convey on their own — typically context, attribution, or a piece of human voice. Most posts won't have one. Sentence-cased, short. The bar is "would I want a reader to read this before looking at the photo?" — if not, leave empty.

### Tag, city, country, artist, year term pages

**`description:`** — fixed prefix per axis, optionally followed by an em-dash and grounded flavour drawn from the post set:

| Axis | Prefix | Example |
|---|---|---|
| Tag | "Street art photos tagged `<term>`" | "Street art photos tagged birds — pink flamingos, a snowy owl pair, an abstract NHS bird, and others." |
| City | "Street art photos from `<city>`" | "Street art photos from Liverpool — the Baltic Triangle, Beatles murals, Liverpool FC tributes." |
| Country | "Street art photos from `<country>`" | "Street art photos from Romania." |
| Artist | "Street art photos by `<artist>`" | "Street art photos by Nathan Bowen — recurring dome-headed figures across London and Liverpool." |
| Year | "Street art photos from `<year>`" | "Street art photos from 2018." |

When the flavour clause is included, each phrase in it must be citable to actual posts in that term (tags, alt text, or body). When there isn't enough material to ground a flavour clause, the bare prefix sentence is sufficient — full stop after the term, no flavour.

### Taxonomy index pages

**`description:`** — explains what the axis organises.

- `/tags/`: "Browse street art photos by the subjects, themes, people, and styles they depict."
- `/tags/by-count/`: "Street art photo tags ordered by how often they appear."
- `/cities/`: "Browse street art photos by city."
- `/countries/`: "Browse street art photos by country."
- `/artists/`: "Browse street art photos by named artist."
- `/years/`: "Browse street art photos by year taken."

### Section and special pages

- Home `/`: description summarising the site (1–2 sentences).
- `/posts/`: "All street art photos, newest first."
- `/colophon/`: description summarising the colophon (only after the colophon body itself exists — out of scope for this pass if still a stub).
- `/404/`: short, friendly redirect-y sentence (e.g. "This page does not exist. Try the homepage or browse by tag.").

## Template changes required

To support `headline:` and the SR-only `title` fallback, two small template edits.

### `themes/notebook/layouts/_default/single.html`

Replace the line:

```
{{ with .Title }}<h2 class="post-title">{{ . }}</h2>{{ end }}
```

with:

```
{{ if .Params.headline }}
  <h2 class="post-title">{{ .Params.headline }}</h2>
{{ else if .Title }}
  <h2 class="post-title sr-only">{{ .Title }}</h2>
{{ end }}
```

Behaviour:
- `headline:` set → visible `<h2>` of the headline.
- `headline:` empty, `title:` set → SR-only `<h2>` of the title.
- Both empty → no `<h2>` (matches today).

### CSS already has `.sr-only`

No CSS change needed. The existing rule visually hides while remaining in the DOM for assistive tech and crawlers.

## Per-term-page description files

Hugo lets you customise a term-page's `description` by creating `content/<plural>/<term>/_index.md` with front matter only. One file per term per axis: ~149 files in total.

The file shape is uniform:

```yaml
---
title: "<term value>"
description: "<the written description>"
---
```

`title:` here is decorative (it inherits anyway), but is included to keep the file self-explanatory.

## Anti-hallucination protocol

During the write, each entry's substantive claims are traced to their source. Concretely, the writer maintains a worked record in the form:

- For each phrase in title/description, the source field it was drawn from.
- If a phrase has no source, it is removed or rewritten.

This isn't shipped — it's a discipline applied during the write. Verification step (below) spot-checks the result.

## Verification

After the writes are applied:

1. Every photo post has `title:` and `description:` populated and non-empty. `headline:` may be empty.
2. Every term-page `_index.md` has `title:` and `description:` populated.
3. Every index / section / special page has `description:` populated (either in front matter or template default).
4. Build succeeds. `make check` passes.
5. Spot-check 15 random posts and 10 random term pages: every substantive claim in title/description is citable to a field in the page's own data. Look for hallucinated content — invented artist names, invented locations, evaluative adjectives, external context.
6. No description starts with "An image of" (alt-text anti-pattern); "Photo of" is the chosen prefix.
7. No US spellings (`color`, `gray`, `favorite`, `center`).

## Out of scope

- Visible title rendering anywhere other than via `headline:` (visual design stays quiet otherwise).
- Tag-page template changes beyond what's needed for description rendering (already in place).
- Writing the colophon body. (The colophon page's description waits until the body exists.)
- A title-derivation tool. All titles are hand-written.

## Commit scope

Two logical commits:

1. **Template change** for the `headline:`/SR-only `title:` fallback in `single.html`. Standalone.
2. **All the writes** in one big commit touching 109 post files, ~149 new term `_index.md` files, ~6 index `_index.md` files, plus a handful of section/special page edits.

If the writes commit becomes too large to review in one go, it may be split per page type at the implementer's discretion — but the editorial taste benefits from doing the writes in one focused pass.
