# Small Observations — Design Spec

**Date:** 2026-05-15
**Status:** Design approved, ready for implementation planning

## Purpose

A personal "small web" blog in the spirit of the [Tiny Awards](https://tinyawards.net) — the small, poetic, handmade, non-commercial web — and the kind of site that might be at home on [Ooh.directory](https://ooh.directory). Single-author point of view. No engagement optimization. Built with Hugo, no theme, hand-written templates and CSS.

We're coding the site with AI assistance, even though the Tiny Awards ethos prizes the handmade. We know that's complicated. The way we square it: the intent, the taste, the editorial decisions, the photos, the words, the design direction — all human. The assistant helps with the typing, catches inconsistencies, and offers options to push back on. Nothing on the site should feel machine-generated; the AI's job is to keep up with the author's hand, not replace it.

The site is bootstrapped with ~100+ smartphone snapshots of street art collected over a decade. May expand to short notes later. Each photo is its own post with metadata (date taken, country, city, optional artist, tags) and optional brief commentary.

## Aesthetic direction

Risograph-zine meets field notebook.

- **Palette:** warm cream paper (`#f4ede0`), near-black warm ink (`#1a1816`), burnt-coral accent (`#c8553d`) for links and emphasis, dusty muted tones for secondary text.
- **Typography:** one self-hosted variable font — Fraunces — exploited across its `opsz`, `wght`, `SOFT`, and `WONK` axes for variety from one file. Small caps and tabular numerals via OpenType features replace a second mono font.
- **Layout:** generous margins, narrow text column, intentional asymmetry where it earns its keep. Photos sit on the page like specimens in a notebook, not gallery prints.
- **Reference mockup:** `mockups/index-lean.html` (canonical) and `mockups/index.html` (earlier, retained for contrast).

## Small-web principles (binding)

These are commitments, not aspirations.

**HTML**
- Semantic, hand-written, minimal nesting. No `<div>` unless it earns its keep.
- Target ≤ 10kb HTML per typical post page.
- View-Source legible. Comments only where they explain the *why*.
- No client-side templating, no SPA shell.

**CSS**
- One hand-written stylesheet, no framework. No PostCSS, no Tailwind, no Bootstrap.
- Target ≤ 8kb gzipped. Inlined in `<head>` (no separate request).
- Modern CSS: custom properties, `clamp()`, container queries if useful. No vendor prefixes.

**Typography**
- Up to two self-hosted variable fonts, woff2, preloaded, `font-display: swap`, system fallback.
- Default plan: Fraunces only (variable, ~30–40kb subset). Combined font budget ≤ 80kb.
- Subset to Latin Extended.
- No Google Fonts CDN in production.

**JavaScript**
- None by default. Every interaction works via HTML + CSS.
- Any future JS must be vanilla, inline, kilobytes not megabytes, and the page must still work without it.

**Images**
- Originals stored outside the repo (user's drive).
- One web-sized JPEG (~1600px long edge, ~80% quality) committed in `assets/img/<year>/<month>/<slug>.jpg`.
- Hugo's image pipeline generates a responsive `srcset` (e.g., 600w / 1000w / 1600w) plus AVIF + WebP + JPEG fallback via `<picture>`.
- `loading="lazy"` on all images below the fold.
- Explicit `width`/`height` to prevent CLS.
- Image-pipeline output cached in `resources/` between builds.

**Third-party**
- No analytics, no fonts CDN, no embeds, no cookie banner.
- Optional later: self-hosted log-based analytics.

**Feeds**
- RSS as a *full-content* feed (commentary + photo link), not a teaser.
- Atom optional alongside.

**Performance budget**
- Homepage: ≤ 50kb total (HTML + CSS + 8 thumbnails).
- Typical post page: ≤ 200kb total (HTML + CSS + one responsive photo at appropriate size).
- LCP under 1s on a decent connection.

**Accessibility**
- Every image needs `alt` text. Ingest script leaves it blank; user fills it in.
- Sufficient contrast across the palette (verify against WCAG AA before launch).
- Default focus outlines visible; if restyled, equally clear.
- Page navigable and readable with CSS disabled.

## Content model

Single Hugo content type under `content/posts/`. Future short-notes use the same type; templates branch on presence of `photo:`.

URL pattern: `/<year>/<month>/<slug>/` where year and month come from the `date` field (which holds the *taken* date — see "Two dates" below).

Per-post front matter (TOML or YAML; spec uses YAML for readability):

```yaml
title: ""                              # optional; templates fall back to date/place
date: 2018-07-14T16:23:00+02:00        # taken date — drives URL & archives
publishDate: 2026-05-15T10:00:00Z      # when post goes live — drives RSS & latest
photo: 2018/07/14-marais-stencil.jpg   # path within assets/img/
countries: [France]                    # taxonomy; one entry, title-cased
cities: [Paris]                        # taxonomy; one entry, title-cased
artists: []                            # taxonomy; empty when unknown; ["Banksy"] otherwise
tags: [stencil, political]             # taxonomy; lowercase
favourites: []                         # taxonomy; e.g. ["favourite"]
years: [2018]                          # taxonomy; derived from date by ingest script
weight: 0                              # ordering within favourites; 0 = unordered
exif:
  camera: "iPhone 7"
  lat: 48.8566
  lon: 2.3522
---

Optional commentary in the body. A few sentences, or empty.
```

Photo is rendered by the template via a `{{ partial "photo.html" . }}` call — not embedded in the markdown body — so layout stays consistent.

### Two dates: taken vs publish

| Use | Field | Why |
|---|---|---|
| URL `/<year>/<month>/<slug>/` | `date` (taken) | Archival meaning |
| Year archive `/years/2018/` (via `years` taxonomy) | `date` | Year derived from this field by ingest |
| Country / city / artist taxonomy listings | `date` | Chronological within a place |
| Post page prominent display ("Paris, July 2018") | `date` | What the reader cares about |
| "Latest posts" page | `publishDate` | What's new on the site |
| RSS feed ordering | `publishDate` | Subscribers want new-to-them |
| Sitemap `lastmod` | `publishDate` | Crawler hint |
| Small "Posted May 2026" line at post bottom | `publishDate` | Colophon transparency |

Hugo natively supports both fields. Templates reference `.Date` and `.PublishDate`.

## Taxonomies

Defined in `hugo.toml`:

```toml
[taxonomies]
  tag = "tags"
  country = "countries"
  city = "cities"
  artist = "artists"
  favourite = "favourites"
  year = "years"
```

Hugo's convention is `singular = "plural"`. The **plural** is the front-matter field name (e.g., `tags:`, `artists:`), and the **plural** is also the URL segment (`/tags/`, `/artists/`).

Standard `categories` taxonomy is **not** defined.

Each taxonomy auto-generates list pages, e.g. `/countries/`, `/countries/france/`, `/artists/`, `/artists/banksy/`, `/favourites/`.

**Capitalization conventions** (enforced by the ingest script where applicable):

| Taxonomy | Convention | Example |
|---|---|---|
| `tags` | lowercase | `stencil`, `political`, `wheatpaste` |
| `artists` | proper name | `Banksy`, `JR`, `Invader` |
| `countries` | proper name | `France`, `United Kingdom` |
| `cities` | proper name | `Paris`, `New York` |
| `favourites` | lowercase, single term | `favourite` |

URLs are always slugified-lowercased by Hugo. Display name comes from the first capitalization encountered, hence the convention.

**Artist taxonomy:** photos with empty `artists: []` do not appear under any artist term. The `/artists/` index lists only known artists; no "unknown" bucket. The artist row in the post template is hidden when the list is empty.

**Year archives:** rather than relying on Hugo's section/permalink mechanics to generate year index pages, `years` is a taxonomy populated by the ingest script from the `date` field. `/years/2018/` lists all photos taken in 2018. The post URL remains `/2018/07/<slug>/` via permalink config — the two coexist cleanly.

**Favourites:** custom taxonomy gives us a native list page at `/favourites/` with RSS and pagination for free. Order via `weight:` (ascending, then by date).

**City disambiguation:** `paris` resolves to one term regardless of country. If a future photo set requires distinguishing (Paris, France vs Paris, Texas), introduce slugged disambiguators like `paris-fr` in front matter; defer until needed.

## Templates

All under `layouts/`. No `themes/` directory.

```
layouts/
├── _default/
│   ├── baseof.html          # shared HTML shell: <head>, masthead, footer
│   ├── single.html          # individual post page
│   ├── list.html            # generic list (catches /posts/, year archives)
│   ├── taxonomy.html        # term page: /countries/france/, /tags/stencil/, etc.
│   └── terms.html           # taxonomy index: /countries/, /tags/, etc.
├── index.html               # homepage
├── favourites/
│   └── taxonomy.html        # override: sorts by weight, custom intro copy
├── partials/
│   ├── masthead.html
│   ├── footer.html
│   ├── photo.html           # responsive <picture> via image pipeline
│   ├── post-meta.html       # date, place, artist row (hides blank fields)
│   └── post-card.html       # compact representation for list pages
└── 404.html
```

Page types and which template renders them:

| Page | Template | Notes |
|---|---|---|
| Homepage `/` | `index.html` | See Homepage structure |
| Latest posts `/posts/` | `_default/list.html` | Reverse-chrono by `publishDate`, paginated |
| Single post | `_default/single.html` | Photo, meta, optional commentary |
| Year archive `/years/2018/` | `_default/taxonomy.html` | Year taxonomy term page |
| Taxonomy term `/countries/france/` | `_default/taxonomy.html` | Sorted by `.Date` (taken) |
| Taxonomy index `/countries/` | `_default/terms.html` | Terms with counts |
| Favourites `/favourites/` | `favourites/taxonomy.html` | Override; sorted by weight then date |
| 404 | `404.html` | Handmade copy, link home |

## Homepage structure

Top to bottom:

1. **Masthead.** Site name set in Fraunces at its expressive optical-size/wonk extremes; small middle-dot in coral; italic tagline below with coral em-dash. No image, no logo, no logo file. Left-aligned, not centered.
2. **Favourites preview.** A 4-column uniform grid of square thumbnails, two rows (8 favourites). Date + place caption under each. "See all favourites →" link at the end.
3. **Browse menu.** A numbered table-of-contents-style list, full width up to `--measure`:
   - Latest posts → `/posts/`
   - By year → `/years/`
   - By country → `/countries/`
   - By city → `/cities/`
   - By artist → `/artists/`
   - By tag → `/tags/`
   - Favourites → `/favourites/`
4. **Footer.** Small caps. Copyright/CC line on one side, RSS / colophon / contact links on the other.

The masthead, both rows of favourites, and the start of the browse menu should fit above the fold on a 1280×800 viewport.

No "blurb" section. No "Now" or "Recently" section.

## Ingest pipeline

A one-shot script — not part of Hugo's build — that transforms a folder of original photos into Hugo content.

**Inputs:** photos dropped in `_ingest/` (gitignored).

**Outputs (per photo):**
- A markdown file at `content/posts/YYYY-MM-DD-slug.md` with prefilled front matter (taken date, country, city, EXIF block, blank `artist:`, blank `title:`, empty `tags:`, default `publishDate`).
- A web-sized JPEG at `assets/img/YYYY/MM/<slug>.jpg` (resized to ~1600px long edge, ~80% quality).
- The original is moved (not copied) out of `_ingest/` to `_ingest/_processed/` so re-runs are idempotent.

**Behavior:**
- Reads EXIF using `exiftool` (or Python `exifread`/`Pillow` — final tool TBD in implementation plan).
- Reverse-geocodes GPS coords to country/city via OpenStreetMap Nominatim (free, polite rate-limit). Cached locally per coord to avoid repeat lookups.
- Tags are normalized to lowercase. Country/city/artist title-cased.
- Photos *without* GPS or date EXIF: logged to `_ingest/_missing-location.log` with filename and what was missing. The photo is **not** processed until the user supplies location manually (the script can be re-run with a sidecar `.yaml` per-photo to inject missing fields).
- Slug: `YYYY-MM-DD-<short-descriptor>` where descriptor is derived from city + a numeric suffix if needed for uniqueness.

**Language:** Python (chosen because `exiftool` wrapper and `geopy`/Nominatim client are mature; final confirmation in implementation plan).

## Image pipeline (build-time)

The `partials/photo.html` partial:
- Reads the `.Params.photo` path relative to `assets/img/`.
- Uses Hugo's `resources.Get` + `image.Resize` / `image.Process` to generate AVIF + WebP + JPEG at 600w, 1000w, 1600w.
- Emits a `<picture>` element with `srcset` and `sizes`, explicit `width`/`height`, `loading="lazy"` (overridable for above-the-fold), and `alt` from front matter.
- Hugo caches outputs in `resources/_gen/` between builds.

## Build & deploy

Out of scope for this design — to be decided during implementation planning. Likely targets: Cloudflare Pages, Netlify, or GitHub Pages. All are static-friendly and free at this scale.

## Repo conventions

**Commit messages** follow conventional commits with a required scope, enforced by a `commit-msg` hook in `.githooks/commit-msg`. To activate after cloning:

```
git config core.hooksPath .githooks
```

Format: `type(scope): subject`

- **Types:** `content`, `feat`, `fix`, `style`, `refactor`, `docs`, `chore`, `build`
  - `content` is a non-standard type used for adding/editing posts (the most common commit on this repo)
  - `style` here means **visual/CSS** changes, not code formatting (we override the canonical CC meaning since CSS dominates "style" work on this site)
- **Scopes:** `home`, `post`, `list`, `partial`, `css`, `font`, `taxonomy`, `ingest`, `photo`, `note`, `config`, `spec`, `mockup`, `deploy`
- **Subject:** lowercase start, no trailing period, ≤72 chars total

Examples:
```
content(photo): add lisbon sardine 2016-05
feat(home): add favourites grid
style(css): tighten masthead spacing
docs(spec): clarify year archive mechanics
fix(ingest): handle photos missing gps
```

Merge, revert, and autosquash (fixup!/squash!/amend!) commits are exempt.

## Out of scope

The following are deliberately deferred:

- **Map view.** A `/map/` page with pins for every photo. Possible later, will need a small JS dependency (e.g., MapLibre + a static tile source). Re-evaluate after the first 100 posts are live.
- **Search.** A small site doesn't need it. Add only if traffic patterns suggest it's wanted.
- **Comments.** No.
- **Newsletter.** No.
- **Analytics.** No by default; if added later, self-hosted, log-based.
- **Short notes.** Same content type, same templates; just don't set `photo:`. Defer adding any until the first one exists.
- **Pagination details** (page size, "older/newer" UI) — decided during implementation.
- **404 copy** — written during implementation.
