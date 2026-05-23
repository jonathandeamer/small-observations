# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal Hugo blog ("Small Observations") and a Python ingest script that turns smartphone photo originals into Hugo posts. Two subsystems sharing only a front-matter schema. The site is in the "small web" tradition — handmade, no JS, single font, minimal CSS, no third-party requests.

Design intent and rationale live in `docs/superpowers/specs/`. Implementation plans live in `docs/superpowers/plans/`. Read these before non-trivial changes — they capture decisions you can't recover from the code alone (e.g., why "favourite" is a plain tag and not a taxonomy).

## Commands — use `make`, never plain `hugo`

Plain `hugo` adds output to `public/` without removing orphans from deleted content, causing stale-build bugs. Always go through the Makefile:

```
make dev          # hugo server (in-memory, doesn't touch public/)
make build        # clean production build + path-warning checks
make check        # build, then run a battery of audits (see "Accessibility & web standards" below)
make clean        # wipe public/, resources/_gen/, .hugo_build.lock
make deploy       # production build then push to S3 + CloudFront invalidate
make deploy-dry   # show what `make deploy` would upload, without uploading
make ingest       # python -m ingest (moves originals to _processed/ on success)
make ingest-dry   # python -m ingest --dry-run
make test         # pytest for the ingest package
make venv         # (re)create .venv with dev deps
```

`make test` runs only ingest tests — there is no template-level test suite. Hugo template correctness is verified manually by `make dev` + browser.

## Commit format — strictly enforced by hook

`.githooks/commit-msg` rejects anything that doesn't match `type(scope): subject`.

- **Types:** `content | feat | fix | style | refactor | docs | chore | build`
  - `content` is a non-standard CC type used for adding/editing posts.
  - `style` here means **visual/CSS**, not code formatting.
- **Scopes:** `home | post | list | partial | css | font | taxonomy | ingest | photo | note | config | spec | mockup | deploy`
- **Subject:** lowercase start, no trailing period, ≤72 chars.

Merge/revert/fixup commits are exempt. If a commit fails the hook, fix the message — don't bypass with `--no-verify`.

## Two distinct subsystems

### 1. Hugo site (`themes/notebook/`, `content/`, `assets/img/`, `hugo.toml`)

- **One local theme**, `themes/notebook/`, containing all design files (layouts, CSS, font). Set via `theme = "notebook"` in `hugo.toml`. This is a *local* theme written from scratch — not a third-party download. Swap by changing the `theme` line, or layer designs with `theme = ["experimental", "notebook"]`.
- **Content vs design split:** `content/` and `assets/img/` (the photos) live at the project root and are shared across themes. `themes/notebook/layouts/`, `themes/notebook/assets/css/`, and `themes/notebook/static/fonts/` are the theme-local design.
- **No JavaScript anywhere.** Interactions are HTML+CSS only.
- **One stylesheet** (`themes/notebook/assets/css/site.css`), inlined into `<head>` via Hugo's resource pipeline. Hand-written, no preprocessor.
- **One self-hosted font** (`themes/notebook/static/fonts/fraunces-latin.woff2`) — Fraunces variable with all four axes (opsz, wght, SOFT, WONK). 134 KB. This exceeds the 80 KB budget in the spec; the overage was a deliberate choice — the SOFT and WONK axes are load-bearing for the masthead and browse-hover effect.
- **Image pipeline** lives in `layouts/partials/photo.html` (post pages, three widths 600/1000/1600) and `gallery-card.html` (thumbnails, two widths 200/400). Both produce WebP + JPEG via `image.Process`. The first gallery card on the homepage is rendered with `eager=true` so its `<img>` gets `loading="eager"` + `fetchpriority="high"` to win the LCP race — preserve that when refactoring the partial. If Lighthouse still suggests further image savings, the next lever would be separate grid-vs-post thumbnail compression, but that is intentionally deferred for now: the gain is small and the complexity is not worth it yet. **AVIF is not used** — Hugo 0.161 extended on macOS doesn't ship with libavif.
- **Taxonomies** are `tags`, `countries`, `cities`, `artists`, `years`. Favourites is a regular `tag` (`favourite`), not its own taxonomy — this was refactored away because `/favourites/favourite/` was an ugly URL.
- **Post URLs** are `/<year>/<month>/<slug>/`. Year and month come from `date` (the *taken* date), not `publishDate`.

### 2. Python ingest (`ingest/`, `tests/`)

A one-shot tool, but designed to keep working for incremental additions. Run via `make ingest` after dropping photos in `_ingest/`. Each module has one job:

- `exif.py` — extract date, GPS, camera from EXIF via Pillow.
- `geocode.py` — reverse-geocode (lat, lon) → (country, city) via OpenStreetMap Nominatim. 1 req/sec rate-limited (their policy); retries once on 429. On-disk cache at `.cache/geocode.json` keyed by coords rounded to 4 decimals (~10m).
- `slug.py` — build `YYYY-MM-DD-<city>` slug, dedupe with `-2`/`-3` suffixes.
- `frontmatter.py` — render Hugo front matter. Hand-written YAML so field order stays stable.
- `resize.py` — JPEG resize to 1600px long edge, q82. Never upscales.
- `pipeline.py` — orchestrate one photo through all of the above.
- `__main__.py` — CLI: scan `_ingest/`, process each, move originals to `_ingest/_processed/` on success (skipped under `--dry-run`).

Tests use real fixture JPEGs regenerated by `tests/conftest.py` at session start (gitignored). Nominatim is mocked in tests.

## Content model — the contract between subsystems

Front matter shape (every post must match this exactly; the ingest script produces it):

```yaml
title: ""
slug: "2018-07-14-paris"        # ALWAYS set, even if title is empty
date: 2018-07-14T16:23:00Z       # taken date — drives URL and archives
publishDate: 2026-05-15T10:00:00Z # publish date — drives RSS feed order; gates whether a post appears in production builds
photo: 2018/07/2018-07-14-paris.jpg
countries: [France]              # empty list [] if unknown
cities: [Paris]                  # empty list [] if unknown
artists: []                      # filled in by hand post-ingest
tags: []                         # filled in by hand post-ingest
years: [2018]                    # derived from date.year
weight: 0                        # used to order within tag/favourite list
exif:
  camera: "iPhone 7"
  lat: 48.8566                   # omitted entirely when GPS missing
  lon: 2.3522
```

Two subtle invariants worth knowing:

- **`slug:` is mandatory.** Hugo's `:slug` permalink token returns empty when title is empty, producing colliding URLs. The ingest always emits `slug:` explicitly. Don't remove this when hand-editing.
- **`years` is a taxonomy populated by the ingest.** It exists because Hugo's permalink config emits a date-based URL but doesn't auto-generate `/<year>/` index pages. The `years` taxonomy gives us `/years/2018/` for free. Hand-written posts must set `years: [<year>]` to appear in archives.

## Content layers — when to reach for alt, tags, or body

Three distinct surfaces carry post content. Each answers a different question; use each only when it actually has something to say.

- **`alt:`** — *What does the image show?* Always required. Describes what a sighted viewer would see, including embedded text and visible artist signatures. Never repeats the title or invents context not in the image. See `docs/superpowers/specs/2026-05-17-alt-text-editorial-design.md` for the editorial criteria.
- **`tags:`** (plus `artists:`, `cities:`, etc.) — *What categories does this post belong to?* Use when the info groups multiple posts in the archive: a recurring theme, a named artist, a place worth filtering by. Reusable, lowercase, plural where natural.
- **Body text** (markdown after the front matter `---` closer) — *What couldn't the camera tell you?* Optional. One short sentence, occasionally two. Use only when there is a specific, unrepeated thing worth saying: provenance ("from the Chatsworth Burning Man exhibition"), attribution not on the wall ("by Banksy"), cultural reference ("a tribute to Basquiat"), how the photo came to be taken, backstory, or what happened after.

**Body-text rules:**
- Don't repeat alt text. The artwork is already described.
- Don't editorialise. No "stunning", "beautiful", "powerful". Show, don't praise.
- If the information is a reusable category, prefer a tag. "Banksy" goes in `artists:`, not body prose.
- Empty is fine. Most posts will have no body.

The decision heuristic: *"if I'd say this to a friend standing next to me looking at the photo, it goes in the body. If it's a category they could later ask me to filter by, it's a tag."*

## Tag taxonomy

The `tags` axis is a single bucket carrying four kinds of entry: **subjects** (what is depicted), **themes** (causes or movements the art engages with), **context** (named people/places/events referenced but not depicted, e.g. `John Lennon` on a "War is Over" piece), and **styles** (distinctive technique — `stencil`, `sticker`, `sculpture`, `Lichtenstein-style`, `Banksy-style`).

**Singletons are fine.** The bar is "plausible future category" — if it could imaginably recur, tag it. Expect the long-term set to sit at 150–250 tags with a long tail of singletons.

**Multi-level tagging.** When a post supports both a broad browse group and a more specific term, tag both. Mural with a warbler → `birds`, `warbler`. Mural depicting the Beatles together → `Beatles`, `John Lennon`, `Paul McCartney`, `George Harrison`, `Ringo Starr`. Footballer in a Liverpool kit → `sports`, `football`, `Liverpool FC`, `<player name>`.

**Generic floor — do not tag:** pure format (`mural`, `painted`, `graffiti`, `wall`, `street art`); generic body parts (`face`, `hand`, `eye`, `head`); generic colours and shapes (`blue`, `pink`, `circle`, `geometric`, plain `abstract`); loose adjectives (`bright`, `large`, `huge`, `small`, `colourful`).

**Naming conventions:**

| Tag kind | Convention | Examples |
|---|---|---|
| Broad browse-group subject | lowercase, plural where natural | `animals`, `birds`, `books`, `flowers`, `sports` |
| Specific depicted subject | lowercase, singular unless normally plural | `hare`, `flamingo`, `skull`, `tree`, `taco` |
| Proper noun (person, team, place, event) | title case, as the world spells it | `John Lennon`, `Liverpool FC`, `Burning Man`, `Chinatown`, `Halloween`, `Barbican` |
| Movement or slogan | verbatim casing | `Black Lives Matter`, `Marriage Equality`, `Slava Ukraini`, `Abolish ICE` |
| Style descriptor | lowercase or title case to match the style's own usage | `stencil`, `sticker`, `sculpture`, `Lichtenstein-style`, `Banksy-style` |
| Theme without a canonical name | lowercase | `climate`, `anti-war`, `housing`, `memorial`, `protest`, `music` |

Pinned cases: `Beatles` not `The Beatles`; `Liverpool FC` not `LFC`; `stencil` (noun), not `stencilled`. Anything that already lives in `cities:`, `countries:`, or `years:` does NOT also need to be in `tags:` — those axes already exist for filtering. `artists:` and `tags:` are *semantically different* (`artists:` = who MADE the art; `tags:` includes who is DEPICTED or REFERENCED) and CAN legitimately overlap on the same post.

**Singleton usefulness.** A one-off tag is worth keeping when it improves search, explains why the post matters, is likely to recur later, or sits under a useful broad group. Remove one-off tags that are too generic, incidental, already covered by alt/body text, or unlikely to help navigation.

**Deriving tags from a new post** (or auditing an existing one): work through the alt text and body text in this order: subjects depicted → themes engaged → context references → style → apply the floor (drop) → apply naming conventions → de-duplicate against city/country/year (NOT artists) → de-duplicate against existing tags (consult `/tags/` index to keep casing/spelling stable).

**Reserved tag names.** `by-count` must never be used as a tag value. The URL `/tags/by-count/` is claimed by the by-count sort variant of the tags index page (see `docs/superpowers/specs/2026-05-17-tags-index-sort-design.md`). Using `by-count` as a tag would collide.

See `docs/superpowers/specs/2026-05-17-tag-taxonomy-design.md` for the full design and rationale.

## Accessibility & web standards

The site aims to remain a "good web citizen" — keyboard-navigable, screen-reader-friendly, valid HTML, well-behaved with crawlers. Several invariants are easy to break by accident; keep them in mind when changing design or templates.

**Automated checks** — all run by `make check`:

- `pa11y` audits the homepage *and* a randomly-picked post page (WCAG 2.1 AA). Suppressions live in `pa11y.json` — decorative `.glyph` spans (the small italic flourishes in section headings) are hidden from the audit because they have no semantic label by design.
- `htmltest` checks internal links and flags `<img>` elements with empty alt text. Currently noisy because alt text isn't written yet — that's tracked separately.
- `xmllint` validates the sitemap at `public/sitemap.xml` and the RSS feed at `public/feed.xml`.
- `vnu` runs the official W3C HTML validator on the homepage + one post when `~/.vnu/vnu.jar` is installed (it is installed on this machine). If missing on another machine, `make check` prints the install command and skips it.

In sandboxed agent sessions, `pa11y` may fail to launch Chromium unless `make check` is rerun with normal local permissions. Treat that as a sandbox/browser-launch issue, not an accessibility failure.

Lighthouse CLI is installed globally (`lighthouse 13.3.0`) for Chrome-style audits, but it is intentionally **not** wired into `make check` — local Hugo perf numbers aren't representative. After a `make deploy` that touches CSS, layout templates, the image pipeline, font loading, or `<head>` content, suggest running `lighthouse https://smallobservations.net --view` against the live URL and flag any score regression versus the previous run.

**Invariants in the design that compliance depends on:**

- **Page-specific `<h1>` everywhere except home.** Every page must carry exactly one `<h1>` describing the page's subject — the post's title on a single post page, the section heading on list/term/taxonomy pages, "Page not found." on the 404. On the homepage the site title ("Small·Observations") is the `<h1>` because the home page *is* the site; on every other page it demotes to `<p class="masthead-title">` (same styling via the class). The pattern lives in `themes/notebook/layouts/partials/masthead.html` — the `{{ if .IsHome }}` branch is what keeps the hierarchy clean. Don't reintroduce a site-title `<h1>` on non-home pages; don't drop the page-specific `<h1>` to `<h2>` because it "looks like a subsection". The CSS selector `.section-head h1, .section-head h2` covers both forms so a sub-section heading on home (where the section-head is `<h2>`) still styles correctly.

- **WCAG AA contrast.** `--muted` (#6e6050) and `--link` (#b34429) were chosen specifically to clear 4.5:1 against `--bg` (#f4ede0). `--link` is a darker variant of `--coral` used for functional links so the brand colour can stay vivid on non-link uses. Re-check contrast (e.g., webaim.org/resources/contrastchecker) before changing any of these.
- **`:focus-visible` keyboard ring** — a 2px coral outline on focused elements. Don't remove the global rule in `site.css`; keyboard users rely on it.
- **Skip-navigation link** — `<a class="skip-nav" href="#main-content">` is the first element in `<body>`, hidden until focused. WCAG 2.4.1 Level A. `<main>` carries the matching `id="main-content"`.
- **Masthead browse nav on every page.** `<nav class="masthead-browse" aria-label="Browse the archive">` with links to `/posts/`, `/tags/`, `/cities/`, `/years/`, `/countries/`, `/artists/` renders on every page (home, post, list, taxonomy, 404). It's a no-JS, no-state main navigation — don't hide it on subsets of pages, don't lazy-load it, don't replace with a hamburger menu. Users landing deep from search rely on it to reach the archive.
- **Canonical URL** — every page emits `<link rel="canonical" href="{{ .Permalink }}">` from `baseof.html`. Don't remove when restructuring `<head>`.
- **Responsive images** — gallery thumbnails use `srcset` at 200w/400w with `sizes` set to actual layout dimensions. Post photos use the full pipeline in `photo.html`. Both produce WebP + JPEG.
- **Open Graph + Twitter Card meta** — generated by `head-og.html`. Falls back to `summary` card when a page has no `photo` param.
- **RSS autodiscovery** — `<link rel="alternate">` in `baseof.html` points to the home feed from every page, not the current page's feed (since only the home output has RSS enabled).

## Things that look wrong but aren't

- **`/_ingest/` and `_ingest/_processed/`** — gitignored. Originals live there outside git history; only the resized JPEGs in `assets/img/` get committed.
- **Test fixtures regenerate per session** — `tests/fixtures/` is gitignored. Conftest writes `with_gps.jpg`, `no_gps.jpg`, `no_exif.jpg` at session start.
- **Mockups directory** — `mockups/index-lean.html` is the canonical visual reference. `mockups/index.html` is an earlier maximalist variant kept for contrast. The live site should match `index-lean.html`.
- **Hugo's `humanize` filter** was removed from `_default/terms.html` and `_default/taxonomy.html`. It treats numeric strings as ordinals (`"2018"` → `"2,018th"`). Don't re-add it without a non-numeric guard.
- **RSS feed** is custom (`themes/notebook/layouts/_default/rss.xml`) and lives at `/feed.xml` only — section/taxonomy/term RSS outputs are disabled in `hugo.toml`. It sorts by `publishDate` descending using `site.RegularPages` (so the feed reflects publishing order, not photo chronology). The `<link rel="alternate">` autodiscovery tag in `baseof.html` always points to the home feed regardless of which page the visitor is on.
- **Sort-order divergence between home/archives and feed.** The home page gallery and section/term archives sort by `.Date` (the photo's *taken* date), so browsing the site feels chronological. The RSS feed sorts by `publishDate` descending so subscribers see newest-published-first. Both are correct — don't try to unify them.
- **`robots.txt`** is a Hugo template (`themes/notebook/layouts/robots.txt`), not a static file, so the `Sitemap:` URL stays in sync with `baseURL`. Don't put one in `static/` — `enableRobotsTXT = true` will override it with an empty default.
- **Photo-only single template.** `_default/single.html` is photo-centric and used for posts (it errors if `.Params.photo` is missing). There are currently no non-photo root pages: the 404 used to be one, but it's now emitted from Hugo's special `layouts/404.html` template (no content file) so the page-layout indirection went away. If you ever add a non-photo root page (about, colophon, etc.), `layouts/page/single.html` is still in the theme as a fallback, but the page's front matter has to declare `type: "page"` to opt into it — Hugo's lookup for root-level pages doesn't auto-discover `layouts/page/`.

- **404 page is emitted by Hugo's built-in handling.** `layouts/404.html` outputs straight to `public/404.html` at the bucket root (no content file required). CloudFront's distribution settings have a Custom Error Response pointing 4xx → `/404.html` with HTTP status 404 — that lives outside the repo, in the AWS console, but it's load-bearing. If you ever rename or remove `/404.html`, update the Custom Error Response. Verifying: hit any broken URL on the live site and check the response body — the headers will look S3-ish (`x-amz-error-code: NoSuchKey`) even when CF is correctly serving `/404.html`, so don't diagnose from headers alone.
- **Per-year `_index.md` files** under `content/years/` are intentional. The `years` taxonomy is auto-populated by the ingest, but each year's term page reads its `title` and `description` from `content/years/<year>/_index.md` — that's where the per-year prose lives. Deleting them strips the prose and falls back to a default heading.
- **`tags/by-count.html` is a separate layout**, not dead code. It renders the `/tags/by-count/` route, an alternate sort of the tags index (see `docs/superpowers/specs/2026-05-17-tags-index-sort-design.md` and the reserved-tag-name note above). The plain `/tags/` page uses `_default/terms.html`; the `by-count` variant needs its own template because Hugo's terms layout doesn't natively support multiple sort views.
- **Favicon trio** in `themes/notebook/static/`: `favicon.svg` (modern), `favicon.ico` (multi-res 16/32/48 fallback), `apple-touch-icon.png` (iOS home-screen, 180×180 with opaque cream background since iOS ignores transparency). All wired up via `<link>` tags in `baseof.html`. The design is the coral star glyph (`✦`) from homepage section headings on the cream page background — keep it in sync if `--coral` or `--bg` ever changes.
- **Cache-Control strategy in `[[deployment.matchers]]`.** Two regimes. Long-cache (`max-age=31536000`) on `.jpg/.jpeg/.png/.gif/.webp/.svg` and `.woff/.woff2` — safe because Hugo's resource pipeline fingerprints filenames, so a new render produces a new URL. Must-revalidate (`public, max-age=0, must-revalidate`) on `.html`, `sitemap.xml`, and `feed.xml` — browsers still cache but always conditional-GET via etag and get a cheap 304 when content is unchanged. The CloudFront invalidation step on deploy covers edges; must-revalidate stops browsers from heuristic-caching stale HTML between deploys. Keep `force = true` out of steady-state matchers: it makes `hugo deploy` re-upload every matching object even when the bytes are unchanged. Use it only as a temporary one-deploy metadata migration (e.g., backfilling a new `cacheControl` value across existing objects), then remove it. The must-revalidate matchers were originally added with `force = true` for exactly that reason on 2026-05-23, then the flag was stripped.
- **Slug changes require aliases.** Photo-post slugs were bootstrapped once (see `docs/superpowers/specs/2026-05-23-photo-slug-bootstrap-design.md`). Any later rename to a post's `slug:` must add an `aliases:` front-matter entry pointing at the old URL path, so Hugo emits a 301 redirect and shared/indexed links keep working. The bootstrap pass itself was the only dispensation — site was soft-launched and barely indexed at the time.

## When in doubt

- For non-trivial changes, read the corresponding spec under `docs/superpowers/specs/` first.
- Remote is `origin` on GitHub (`jonathandeamer/small-observations`). Don't push or open PRs unless explicitly asked; commits stay local until the user invites the push.
- Don't introduce npm, Node, Tailwind, PostCSS, or any JS toolchain **into the site itself**. The published site has no runtime JS and no third-party requests — that's a design constraint, not a tooling preference. Local dev/audit tools (including Node-based CLIs like pa11y) are fine.
- **Canonical domain is apex-only:** `https://smallobservations.net/`. No `www.` subdomain is published or supported. RSS feeds, sitemap, Open Graph tags, canonical URLs, and the `robots.txt` Sitemap line all derive from this single `baseURL` in `hugo.toml`.
- **Open Graph tags** are generated by `themes/notebook/layouts/partials/head-og.html` and called from `baseof.html`. Posts use `.Params.photo` for `og:image` and `.Params.alt` for `og:image:alt` / `twitter:image:alt`. Description is `.Description | default site.Params.description`. `og:locale = en_GB` (Facebook uses the underscore form, distinct from HTML `lang="en-gb"`). The homepage has no `.Params.photo`, so the partial picks the first favourite by weight (same selection logic as the home gallery's first card) and reuses that photo's resize pipeline for the OG image. Per-post descriptions can be added via a `description:` field in front matter — the ingest does this from alt text.
- **British English on the public-facing site.** Any AI-generated text that will appear on the site itself (post titles, alt text, descriptions, tags, page copy, OG descriptions, RSS-visible strings) must use British spelling and idioms — "colour" not "color", "favourite" not "favorite", "centre" not "center", "organisation" not "organization", "—" / single quotes per British convention. Doesn't apply to commit messages, code comments, plan/spec docs, or this file — those are working notes, not public output.
