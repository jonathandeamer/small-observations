# Small Observations

[![live](https://img.shields.io/badge/live-smallobservations.net-b34429)](https://smallobservations.net)
[![Built with Hugo](https://img.shields.io/badge/built_with-Hugo-ff4088?logo=hugo&logoColor=white)](https://gohugo.io)

> Source of [smallobservations.net](https://smallobservations.net) — a web notebook of street art I've enjoyed.

## The site

A [Hugo](https://gohugo.io) build with one local theme written from scratch. No JavaScript, one stylesheet, one self-hosted variable font ([Fraunces](https://fonts.google.com/specimen/Fraunces)), no third-party requests. Photos run through Hugo's image pipeline at build time to produce a WebP + JPEG `srcset` per post.

## The ingest pipeline

A small Python tool that turns a phone photo into a Hugo post. For each image in `_ingest/`, it reads EXIF (date, GPS, camera) with [Pillow](https://python-pillow.org), reverse-geocodes the coordinates against [OpenStreetMap Nominatim](https://nominatim.org), builds a `YYYY-MM-DD-<city>` slug, resizes the JPEG to 1600px on the long edge, and writes the post with stable front matter. Originals move to `_ingest/_processed/` and never enter git; the resized JPEGs do. Nominatim calls are rate-limited to their 1 req/sec policy and cached on disk by rounded coordinates.

## Running it

Everything goes through `make` — never plain `hugo` (it leaves orphans in `public/`).

| Command         | What it does                               |
|-----------------|--------------------------------------------|
| `make dev`      | Local dev server                           |
| `make build`    | Clean production build                     |
| `make check`    | Build + content / accessibility / HTML audits |
| `make ingest`   | Process new photos in `_ingest/`           |
| `make test`     | Run ingest tests                           |
| `make deploy`   | Build and push to S3 + CloudFront          |

## Auditing

`make check` builds the site and runs a battery of checks.

**Content shape** (Python scripts in `scripts/`):

- Front-matter schema on every photo post
- Slug uniqueness across `content/posts`
- Alt text present on every photo
- Rendered-page metadata: canonical URL, OG tags, taxonomy links
- RSS feed and sitemap URL contracts

**Standards / accessibility** (third-party CLIs):

- [pa11y](https://pa11y.org) — WCAG 2.1 AA on the homepage and a random post page
- [htmltest](https://github.com/wjdp/htmltest) — internal link checker; also flags empty `<img>` alt
- [vnu](https://validator.github.io/validator/) — the W3C HTML validator
- `xmllint` — well-formedness check on `sitemap.xml` and `feed.xml`

[Lighthouse](https://github.com/GoogleChrome/lighthouse) isn't wired in — local Hugo perf numbers aren't representative of the deployed site.

## Deploy

`make deploy` uses Hugo's built-in deployer to push to an S3 bucket in `eu-west-2` fronted by CloudFront, and invalidates the changed paths. The apex domain (`smallobservations.net`) is the only published host.

Cache headers are set per-file in `hugo.toml`:

- Images and fonts get one-year `max-age` — Hugo fingerprints their filenames, so a new render is a new URL.
- HTML, the RSS feed, and the sitemap revalidate on every request, so a deploy is visible immediately.

## Notes

- AVIF isn't used (Hugo extended on macOS doesn't ship with libavif)
- URL year/month come from the photo's taken date, not the publish date
- Commit messages are validated by a git hook (conventional-commits subset)

## Development

This project is built collaboratively with AI coding agents — primarily Claude Code, with Codex used for second opinions and parallel work. The process leans on the [Superpowers](https://github.com/obra/superpowers) skill set: specs in `docs/superpowers/specs/`, implementation plans in `docs/superpowers/plans/`, both checked in. Visual work was prototyped with the `frontend-design` skill and the brainstorming skill's *visual companion*; canonical mockups live in `mockups/`.
