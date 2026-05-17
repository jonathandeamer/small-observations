---
title: "Colophon"
type: "page"
description: "How this site is made, hosted, checked, and kept small."
---

Small Observations is a static site, built deliberately plainly. No client-side
JavaScript, no third-party fonts, no embeds, no trackers. The published pages
are HTML and CSS, with photographs rendered as responsive images.

The site is built with [Hugo](https://github.com/gohugoio/hugo). The theme is
local to this repository, written from scratch, with one hand-written stylesheet
inlined into the page head. The typeface is
[Fraunces](https://github.com/undercasetype/Fraunces), self-hosted as a single
variable WOFF2 file and used for both text and the masthead.

Photos are prepared by a small local ingest script written in
[Python](https://github.com/python/cpython). It uses
[Pillow](https://github.com/python-pillow/Pillow) for image and EXIF handling,
and [Nominatim](https://github.com/osm-search/Nominatim) for reverse-geocoding
where GPS data is available. The ingest tests use
[pytest](https://github.com/pytest-dev/pytest) and
[Piexif](https://github.com/hMatoba/Piexif).

The local check suite uses [htmltest](https://github.com/wjdp/htmltest) for
internal links, [Pa11y](https://github.com/pa11y/pa11y) for accessibility,
[vnu](https://github.com/validator/validator) for HTML validation, and
[xmllint](https://gitlab.gnome.org/GNOME/libxml2) for RSS and sitemap XML.
[Lighthouse](https://github.com/GoogleChrome/lighthouse) is installed too, but
is only run manually against the live site, since local development performance
numbers are not very meaningful.

Hosting is on AWS S3 and CloudFront. Analytics, when enabled, will be
log-based rather than script-based: CloudFront access logs processed locally
with [GoAccess](https://github.com/allinurl/goaccess), with IP addresses
anonymised and raw logs expired after a short retention period.

The photographs, selection, metadata, and public copy are by Jonathan. AI tools
helped with implementation, consistency checks, and first-pass drafting, but the
editorial decisions and final wording are human.
