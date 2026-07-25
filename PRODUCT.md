# Product

## Register

brand

## Users

A single author (Jonathan) and the small audience of people who stumble onto a personal "small web" site — via [Ooh.directory](https://ooh.directory), a Tiny Awards-adjacent link, an RSS reader, or a search result that lands them deep on one photo.

They are not customers and there is no funnel. The reader's job is simply to *look* — to browse a decade of street-art snapshots like turning the pages of someone's field notebook, follow a tag or a city if a thread catches their eye, and leave when they're done. No account, no goal, no conversion. The author's job is to publish without engagement pressure and keep the whole thing feeling handmade.

## Product Purpose

"Small Observations" is a personal Hugo blog presenting ~100+ smartphone snapshots of street art collected over a decade, each photo its own post with metadata (taken date, country, city, optional artist, tags) and optional one-or-two-sentence commentary. It exists as an act of the small, poetic, non-commercial web — a deliberate counterweight to engagement-optimised, JavaScript-heavy, surveillance-funded sites.

Success looks like: a site that loads in under a second, works with CSS or JS disabled, reads cleanly in View Source, and never once feels machine-generated despite being built with AI assistance. The photos and words are the product; the design's job is to frame them like specimens without ever upstaging them.

## Brand Personality

**Risograph-zine meets field notebook.** Handmade, poetic, quietly confident, unhurried. Warm rather than clinical; opinionated rather than neutral; intimate rather than institutional.

Three words: **handmade, warm, restrained.**

Voice: a single human point of view. Captions and commentary observe, they never sell or editorialise ("show, don't praise" — no "stunning", "beautiful", "powerful"). The interface should feel like it was set by hand by someone with taste and a budget of zero kilobytes to spare. Expressive where it earns it (the Fraunces masthead pushed to its optical-size and WONK extremes, the coral em-dash and middle-dot), plain everywhere else.

## Anti-references

- **Anything that reads as machine-generated.** This is the cardinal anti-reference. The AI assists the typing and catches inconsistencies; it must never make the site feel templated, auto-spun, or off-the-shelf.
- **Engagement-optimised commercial web.** No infinite scroll, no related-content rails, no "you might also like", no popups, no cookie banner, no newsletter capture, no social share buttons.
- **SaaS / startup landing-page grammar.** No hero-metric blocks, no identical icon-heading-text card grids, no uppercase tracked eyebrows above every section, no gradient text, no glassmorphism, no numbered "01 / 02 / 03" section scaffolding.
- **Gallery-print preciousness.** Photos sit on the page like notebook specimens, not framed fine-art prints on a white-cube wall.
- **Framework-default polish.** No Tailwind/Bootstrap look, no third-party theme, no Google Fonts CDN, no JS toolchain in the published site.

## Design Principles

1. **Nothing should feel machine-made.** Every editorial and design decision is the author's hand; AI keeps up with that hand, it doesn't replace it. When a choice would make the site feel auto-generated, don't make it.
2. **Constraint is the aesthetic.** One stylesheet, one font, no JavaScript, tight performance budgets (≤50 KB homepage, ≤200 KB post, LCP <1s). The limits aren't obstacles to design around — they *are* the design. Reach for what existing CSS and the variable-font axes can do before adding anything.
3. **The photo is the subject; the frame stays quiet.** Typography, colour, and motion serve the image and the words. Expressive flourishes are rationed to a few load-bearing spots (masthead, accents); everything else recedes.
4. **Show, don't praise.** Copy observes and attributes; it never editorialises or sells. British English throughout on anything public-facing.
5. **A good web citizen.** Semantic hand-written HTML, keyboard-navigable, screen-reader-friendly, readable with CSS off, polite with crawlers. View-Source legible — the markup is part of the craft.

Baseline-with-evolution: these principles record the settled direction *and* license tasteful refinement within the small-web ethos. Evolve within the constraints (better type rhythm, sharper spacing, a more intentional accent moment); never relax the constraints themselves (no JS, no framework, no third-party requests, no machine-made feel) without an explicit decision.

## Accessibility & Inclusion

- **WCAG 2.1 AA** is the standing target, audited by `make check` (pa11y on home + a random post).
- Body and functional-link colours (`--ink`, `--muted` #6e6050, `--link` #b34429) were chosen specifically to clear 4.5:1 against the cream `--bg` (#f4ede0); re-verify before changing any of them.
- Every image requires real `alt` text describing what a sighted viewer sees.
- Exactly one page-specific `<h1>` per page; visible `:focus-visible` ring; skip-nav link; archive browse-nav on every page.
- No JavaScript dependency — every interaction works with HTML + CSS, and the page stays navigable and readable with CSS disabled.
- Reduced motion: there is essentially no motion today; any future motion must ship a `prefers-reduced-motion: reduce` alternative.
