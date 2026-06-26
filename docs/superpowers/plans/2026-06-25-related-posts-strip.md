# Related-posts Strip Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Related" strip to the foot of each single post page showing up to three posts that share an artist, tag, or city, omitted entirely when nothing relates.

**Architecture:** Configure Hugo's built-in `[related]` similarity engine over the `artists`/`tags`/`cities` indices, render the matches through the existing `gallery-card.html` partial in a new `related.html` partial, and place it in `single.html` between the post meta and the colophon. CSS reuses the existing gallery grid.

**Tech Stack:** Hugo 0.161 extended, Go templates, hand-written CSS (no preprocessor, no JS).

**Spec:** `docs/superpowers/specs/2026-06-25-related-posts-strip-design.md`

## Global Constraints

- No JavaScript and no third-party requests on the published site — HTML + CSS only.
- Build only via `make` (`make build`, `make check`, `make dev`) — never plain `hugo`.
- No template-level unit tests exist; correctness is verified by `make build`, `make check` (pa11y/htmltest/vnu), and `make dev` + browser. This plan follows that convention.
- Commit format enforced by hook: `type(scope): subject` — lowercase subject start, no trailing period, ≤72 chars. Scopes used here: `config`, `partial`, `css`. Types: `feat`, `style`.
- Public-facing copy is British English. The only new copy is the heading "Related".
- All work on branch `feat/related-posts` (already created).
- Preserve the LCP invariant: the post photo is the LCP image; related cards must be lazy (`eager=false`), never eager/`fetchpriority=high`.

---

### Task 1: Related config, partial, and placement

Wires up the `[related]` engine, the rendering partial, and its placement on the post page. Deliverable: the strip renders up to three related cards on posts that have relations and is absent on posts that don't. Unstyled (or minimally styled) is acceptable at the end of this task — Task 2 handles CSS.

**Files:**
- Modify: `hugo.toml` (add a top-level `[related]` block; place it near `[taxonomies]`/`[permalinks]`, before `[outputs]`)
- Create: `themes/notebook/layouts/partials/related.html`
- Modify: `themes/notebook/layouts/_default/single.html` (insert partial call between line 19 `post-meta.html` and line 21 `<p class="post-colophon">`)

**Interfaces:**
- Consumes: existing `gallery-card.html` partial, called as `partial "gallery-card.html" (dict "page" $p "eager" false)`.
- Produces: `partial "related.html" .` — takes the current page as context, renders an `<aside class="related">` or nothing.

- [ ] **Step 1: Add the `[related]` config block to `hugo.toml`**

Insert after the `[permalinks]` block (after line 20), before the `# Output formats` comment:

```toml
# Related-posts similarity engine (drives the "Related" strip on post pages).
# toLower MUST stay false: tags/artists are mixed-case by design (e.g.
# "John Lennon", "Liverpool FC") and index names must match taxonomy names
# exactly. includeNewer=true so relations work both directions in the archive.
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

- [ ] **Step 2: Create the `related.html` partial**

Write `themes/notebook/layouts/partials/related.html`:

```go-html-template
{{/*
  Renders a "Related" strip of up to three posts that share an artist, tag,
  or city with the current post, ranked by Hugo's [related] engine.
  Caller passes the page as the context. Renders nothing when there are no
  related posts — no heading, no wrapper.

  Cards reuse gallery-card.html with eager=false: the LCP image is the post
  photo above, so related thumbnails must never claim fetchpriority.
*/}}
{{ $related := first 3 (site.RegularPages.Related .) }}
{{ with $related }}
<aside class="related" aria-label="Related posts">
  <h2 class="related-head">Related</h2>
  <div class="gallery related-grid">
    {{ range . }}
      {{ partial "gallery-card.html" (dict "page" . "eager" false) }}
    {{ end }}
  </div>
</aside>
{{ end }}
```

- [ ] **Step 3: Place the partial in `single.html`**

In `themes/notebook/layouts/_default/single.html`, between the `post-meta.html` call and the colophon paragraph, so it reads:

```go-html-template
  {{ partial "post-meta.html" . }}

  {{ partial "related.html" . }}

  <p class="post-colophon">
```

- [ ] **Step 4: Build and verify the strip renders**

Run: `make build`
Expected: build succeeds with no errors and no new path warnings.

Then identify a post with relations and one without:

Run: `grep -rl "artists:" content | head -1` to find a post that has an artist set (likely to have related matches via the artists index).

Inspect its built page for the strip:

Run: `grep -c 'class="related"' public/<year>/<month>/<slug>/index.html`
Expected: `1` for the post with relations.

- [ ] **Step 5: Verify the strip is absent when nothing relates**

Pick a post with no `artists`, minimal/unique `tags`, and a unique city (or temporarily inspect one whose related set is empty). Confirm:

Run: `grep -c 'class="related"' public/<that-post>/index.html`
Expected: `0` — the `{{ with $related }}` guard omits the whole block.

If every post happens to have relations, confirm the guard logic instead by reading the rendered output of the lowest-overlap post and checking there is no empty `<aside>` with zero cards.

- [ ] **Step 6: Browser check**

Run: `make dev`
Open a post with relations: confirm up to three cards appear below the meta, above "← all posts", each linking to the right post with the date·place caption. Open a post without relations: confirm no strip. Stop the dev server.

- [ ] **Step 7: Commit**

```bash
git add hugo.toml themes/notebook/layouts/partials/related.html themes/notebook/layouts/_default/single.html
git commit -m "feat(config): add related-posts engine and strip to post pages"
```

---

### Task 2: Style the related strip

Gives the strip its visual treatment: a quiet footer block separated from the meta above, heading consistent with the site, cards reusing the gallery grid. Deliverable: the strip looks intentional in the browser and passes `make check`.

**Files:**
- Modify: `themes/notebook/assets/css/site.css` (add a `.related` block; reuse existing `.gallery` grid rules for `.related-grid`)

**Interfaces:**
- Consumes: existing `.gallery` grid CSS and the section-heading/glyph styling already in `site.css`.
- Produces: `.related`, `.related-head`, `.related-grid` style rules.

- [ ] **Step 1: Inspect existing gallery and section-heading CSS**

Run: `grep -n "\.gallery\|section-head\|\.glyph" themes/notebook/assets/css/site.css`
Read the matched rules so the new styles reuse the grid and match the heading treatment rather than duplicating or clashing.

- [ ] **Step 2: Add the `.related` styles**

Append to `themes/notebook/assets/css/site.css` a block that:
- Gives `.related` top separation from the meta above — a hairline top rule (use the existing border/rule colour variable already in the file, e.g. the same one used for other foot separators) and top margin/padding consistent with the page-foot rhythm.
- Styles `.related-head` to match the site's section-heading register (reuse the existing heading style/glyph if it sits cleanly; otherwise a lighter standalone heading). Keep it quieter than the post title.
- Maps `.related-grid` onto the existing gallery grid layout so cards, gaps, and responsive `sizes` match the homepage. If `.gallery` already supplies the grid, `.related-grid` needs no separate grid declaration — only any width cap so three cards read as one short row.

Match the surrounding CSS idiom (custom properties, spacing scale, comment density) already in `site.css`. Do not introduce a preprocessor or new tooling.

- [ ] **Step 3: Browser check the styling**

Run: `make dev`
Open a post with relations: confirm the strip reads as a quiet footer block — separated from the meta, heading in keeping with the site, up to three cards in one tidy row, not competing with the post photo. Check mobile width (two-up grid like the homepage). Stop the dev server.

- [ ] **Step 4: Run the full audit suite**

Run: `make check`
Expected: build succeeds; pa11y (homepage + random post), htmltest, xmllint, and vnu pass. If pa11y fails to launch Chromium in a sandbox, rerun with normal local permissions — that's a browser-launch issue, not an accessibility failure (per CLAUDE.md). The new `<aside aria-label="Related posts">` + `<h2>` must not introduce a11y or HTML-validation errors.

- [ ] **Step 5: Commit**

```bash
git add themes/notebook/assets/css/site.css
git commit -m "style(css): style the related-posts strip"
```

---

## Notes for the implementer

- **Empty-strip behaviour is the load-bearing detail.** The `{{ with $related }}` guard is what makes the strip vanish on posts with no relations. Do not replace it with an `{{ if }}` that still emits the `<aside>` wrapper — an empty labelled landmark is an a11y smell and a visual gap.
- **`site.RegularPages.Related` (not `.Site.Pages`)** keeps the candidate set to published posts only, respecting the existing `publishDate` production gating. Do not switch to `.Pages` or `.Site.AllPages`.
- **`first 3`** caps the set; the spec chose three deliberately (one short row). Don't raise it without revisiting the spec.
- If `make build` warns that no pages have related matches at all, double-check the index `name` values exactly equal the taxonomy names in `[taxonomies]` (`tags`, `artists`, `cities` — note these are the *taxonomy* names, the plural forms).
