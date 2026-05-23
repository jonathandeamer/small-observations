# Site audit findings — 2026-05-23

Full review of the rendered static site (`public/`) across performance, accessibility, navigation, SEO, web standards, and content consistency. `make check` (pa11y + htmltest + vnu + xmllint) was passing throughout — these findings are issues the automated suite doesn't catch.

## Fixed in this pass

### 1. `/404.html` was missing at the site root — **fixed**
**Symptom:** `themes/notebook/layouts/404.html` is a perfectly good template (browse links to home/posts/years/countries/cities/tags), but `content/404.md` with `type: "page"` was overriding Hugo's special 404 handling. Output went to `/404/index.html` instead of `/404.html`. CloudFront's "Custom error responses" was already configured to serve `/404.html` — but the file didn't exist, so broken URLs were falling through to S3's default response.

**Fix:** Deleted `content/404.md`. Hugo now emits `layouts/404.html` straight to `public/404.html`. CloudFront's Custom Error Response (configured outside the repo, in the AWS distribution settings) picks it up automatically: verified live by fetching several fresh broken URLs (`/totally-random-…/`, `/2099/01/fake-post/`, `/tags/this-tag-does-not-exist/`, `/cities/atlantis/`) — all return HTTP 404 with the friendly `/404.html` body (`<title>404: page not found · Small Observations</title>`, `<h1>Page not found.</h1>`, masthead browse nav, explore links).

> Diagnostic note for future audits: when CloudFront's Custom Error Response is active, S3's headers still pass through (`server: AmazonS3`, `x-amz-error-code: NoSuchKey`, etc.) even though the *body* is the custom error page. Don't diagnose from headers alone — fetch the body and inspect the `<title>` / `<h1>`.

### 2. Insecure HTTP link in every page footer — **fixed**
**Symptom:** `<a href="http://jonathandeamer.com">Jonathan</a>` on all 271 HTML pages — mixed-content warnings, extra redirect hop.

**Fix:** Changed to `https://` in `themes/notebook/layouts/partials/footer.html`.

### 3. `lang` attribute inconsistency — **fixed (and switched to British English)**
**Symptom:** Regular pages emitted `lang="en"`; the two Hugo alias pages emitted `lang="en-us"`. The site's editorial voice is British English (per CLAUDE.md), so neither was right.

**Fix:** In `hugo.toml`, set `defaultContentLanguage = "en-gb"` and `locale = "en-gb"` (replacing the old `locale = "en-us"`). Updated the `default` fallback in `baseof.html` to `"en-gb"`. All pages — including aliases — now emit `lang="en-gb"`. The RSS feed's `<language>` element is now `en-gb` too. Note: Hugo deprecated `languageCode` in favour of `locale` as of v0.158, so `locale` is the supported field going forward.

### 4. Browse navigation only on the homepage — **fixed**
**Symptom:** `latest | tags | cities | years | countries | artists` only rendered when `.IsHome` was true. A user landing on a deep post via Google had no path to the archive without going home first.

**Fix:** Removed the `{{ if .IsHome }}` guard around `<nav class="masthead-browse">` in `themes/notebook/layouts/partials/masthead.html`. The nav now appears on every page, including 404.

### 5. `/tags/by-count/` and `/tags/` were duplicate content — **fixed**
**Symptom:** Both pages had `<title>Tags · Small Observations</title>` and identical `<h1>` content. They self-canonicalised, so Google could conflate them.

**Fix:** Updated `themes/notebook/layouts/tags/by-count.html` to produce `<title>Tags by count · Small Observations</title>` and `<h1>Tags by count</h1>`. Distinct from the alphabetical `/tags/` page.

### 6. Site title was the `<h1>` on every page — **fixed**
**Symptom:** Every one of the 273 pages had `<h1>Small·Observations</h1>` as its only `<h1>`. Per-page subjects (post titles, "Tag: animals", "Latest posts") were `<h2>`. Bad for SEO — search engines couldn't tell pages apart by heading. The post title on single pages was also `.sr-only`, so visually there was no page heading at all.

**Fix:**
- `masthead.html` — site title is `<h1 class="masthead-title">` on the homepage (where it's correct) and `<p class="masthead-title">` everywhere else. New `.masthead-title` class carries the styling (was `.masthead h1`).
- `_default/single.html` — post title is now `<h1 class="post-title">` (with `sr-only` preserved when there's no visible headline). The `.post-title` class already drove the styling, so no CSS change needed.
- `_default/list.html`, `_default/terms.html`, `_default/taxonomy.html`, `tags/by-count.html`, plus the per-taxonomy `tag/terms.html`, `city/terms.html`, `country/terms.html`, `year/terms.html`, `artist/terms.html` — all section-head `<h2>` → `<h1>`.
- `404.html` — `<h2>` → `<h1>`.
- `page/single.html` (the legacy non-photo page template, now only used historically) — `<h2>` → `<h1>`.
- `site.css` — `.section-head h2` selector widened to `.section-head h1, .section-head h2` (the home page still uses `<h2>` for sub-section heads like "A few favourites"). `.notfound h2` → `.notfound h1`.

The home page hierarchy stays clean (`<h1>` = site, `<h2>` = sections). Every other page now has a meaningful page-specific `<h1>`.

### 7. No `og:image:alt` on social cards — **fixed**
**Symptom:** Every post had `og:image` but no alt text for it. Posts already carry rich `alt` strings; nothing was being passed through.

**Fix:** `head-og.html` now emits `<meta property="og:image:alt">` and `<meta name="twitter:image:alt">` whenever the picked photo has an `alt` value.

### 8. No `og:locale` — **fixed**
**Symptom:** No locale declared in OG, so Facebook (and any other OG consumer) fell back to defaults.

**Fix:** `head-og.html` now emits `<meta property="og:locale" content="en_GB">` on every page (note: Facebook uses underscore form `en_GB`, not the dash form used for HTML `lang`).

### 9. Homepage had no `og:image` — **fixed**
**Symptom:** The home URL fell back to a `summary` Twitter card with no image. Shared on social, the most important URL on the site looked bare.

**Fix:** `head-og.html` now picks the first favourite by weight for the homepage and uses its photo (plus alt text) for OG and Twitter image meta. The homepage uses the same image-resize pipeline (1200px wide, q82) as post pages, so the OG image inherits long-cache headers.

### 10. No `Cache-Control` header on HTML, sitemap, or feed — **fixed (found via post-deploy crawl)**
**Symptom:** Deploy matchers in `hugo.toml` set long-cache on images and fonts but nothing was set on `.html` / `sitemap.xml` / `feed.xml`. The origin returned no `Cache-Control`, so both CloudFront and browsers fell back to heuristic TTLs (typically hours). CloudFront's invalidation step on deploy handled the edges, but browser caches could continue serving stale HTML.

**Fix:** Added three deploy matchers emitting `Cache-Control: public, max-age=0, must-revalidate` for HTML, sitemap, and feed. Browsers still cache, but always send a conditional GET — etag-based, returns `304 Not Modified` cheaply (verified live). Images and fonts keep their 1-year long-cache. The matchers were deployed once with `force = true` to backfill the metadata on existing S3 objects; that flag is removed for steady state per CLAUDE.md's deployment-matcher note.

## Findings not addressed (yet)

Listed roughly by impact so future passes can pick what to do next.

### Medium-impact

- **11. Hugo aliases use meta-refresh redirects, not real 301s.** `2025/08/new-york-banksy-child-brush/` and `/posts/page/1/` emit `<meta http-equiv=refresh content="0; url=…">`. Browsers and Googlebot generally treat these as 301-equivalent but it isn't ideal. Proper 301s would need CloudFront redirect rules.

- **12. Long taxonomy/term pages don't paginate.** `/cities/london/` has 48 cards on one page; `/tags/animals/` has 39. Only `/posts/` paginates. Lazy-loading limits the cost, but pages will keep growing.

### Polish / accessibility nits pa11y doesn't catch

- **13. Bare `|` pipe characters between masthead browse links.** Screen readers will read each one ("pipe" or "vertical bar"). Either wrap in `<span aria-hidden="true">` or replace with CSS `::after` borders/dots. Now that the nav is shown on every page (#4 above), this is more pages-per-user-affected than before.

- **14. Decorative `<span class="glyph">✦</span>` and masthead `<span class="amp">·</span>` lack `aria-hidden="true"`.** Screen readers announce them ("black four-pointed star", "middle dot"). `pa11y.json` suppresses the glyph from automated audits but the underlying SR experience isn't changed. Adding `aria-hidden` lets the pa11y suppression go.

- **15. No `<meta name="theme-color">`.** Would tint the Android Chrome address bar and Safari tab strip to `--coral` or `--bg`.

### Polish / SEO / structure

- **16. Two tag URLs use non-standard characters:** `/tags/j%C3%BCrgen-klopp/` (UTF-8 percent-encoded `ü`) and `/tags/mr.-monopoly/` (period in path). Both legal, but cleaner slugs (`jurgen-klopp`, `mr-monopoly`) would be more portable across link previewers and older clients.

- **17. No JSON-LD structured data.** A `BlogPosting` / `ImageObject` schema per post (title, datePublished, image, alt, geo) would unlock rich snippets. Not essential for a personal site, but inexpensive to add.

- **18. RSS items duplicate the description.** It appears as `<description>` and as the first paragraph inside `<content:encoded>`. Some readers will show it twice. Could remove from `<content:encoded>` (it's already in the post body) or from `<description>`.

### Knowingly accepted (intentional design, not bugs)

- 8.5 KB of inline CSS × 273 pages — duplicated, but the single-file-per-page design intent is documented in CLAUDE.md.
- Paginated `/posts/page/N/` self-canonicalise to `/posts/` — fine, every individual post is in the sitemap.
- `humanize` filter previously stripped from year/taxonomy templates — left out by design.
- Single-page layouts (`_default/single.html` is photo-only, `page/single.html` exists for non-photo root pages) — documented in CLAUDE.md.

## Verification

Local `make check` audits passed throughout (all fixes were either in-template or config-only):

- `htmltest` — 273 documents, no broken internal links.
- `pa11y` — no issues on homepage or sample post.
- `vnu` — HTML validation clean on homepage + post.
- `xmllint` — sitemap (265 URLs) and RSS feed both valid.
- ingest tests not run (no Python changes in this pass).

Live-site verification after deploy:

- 18 hand-picked entry points (home, all archive indexes, paginator pages, feeds, sitemap, robots, sample term pages) — all 200.
- 44 random sitemap URLs — all 200.
- 126 internal links from home + a post + tags index — all 200.
- UTF-8 tag URL (`/tags/jürgen-klopp/` → `/tags/j%C3%BCrgen-klopp/`) and dot-in-path URL (`/tags/mr.-monopoly/`) — both 200.
- Four fresh broken URLs — all return HTTP 404 with the friendly `/404.html` body (CloudFront Custom Error Response confirmed working).
- Cache-Control headers — HTML/sitemap/feed/404 carry `public, max-age=0, must-revalidate`; images and fonts keep `max-age=31536000`. Conditional GET with matching etag returns `304 Not Modified`.
- Lighthouse (live homepage): Performance 76, Accessibility 100, Best Practices 100, SEO 100, Agentic Browsing 100. LCP 2.8 s (mostly Style & Layout cost from the 4-axis variable font and the inline CSS — both documented design trade-offs).
