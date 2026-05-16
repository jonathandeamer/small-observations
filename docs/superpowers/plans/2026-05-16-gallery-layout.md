# Gallery Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the horizontal card layout on taxonomy term and list pages with a square photo grid matching the homepage favourites gallery, and fix sort order to date taken throughout.

**Architecture:** Extract the homepage fav-card markup into a shared `gallery-card.html` partial; update `index.html`, `taxonomy.html`, and `list.html` to use it; rename the CSS class from `.favourites-grid` to `.gallery-grid`; delete the now-unused `post-card.html` partial and its CSS.

**Tech Stack:** Hugo templates, hand-written CSS. No JS. No test suite for templates — verification is `make dev` + browser inspection, and `make check` for the full audit.

---

### Task 1: Extract `gallery-card.html` partial and update `index.html`

**Files:**
- Create: `themes/notebook/layouts/partials/gallery-card.html`
- Modify: `themes/notebook/layouts/index.html`
- Modify: `themes/notebook/assets/css/site.css` (rename `.favourites-grid` → `.gallery-grid`)

- [ ] **Step 1: Create `gallery-card.html`**

Create `themes/notebook/layouts/partials/gallery-card.html` with this exact content:

```html
{{ $rel := printf "img/%s" .Params.photo }}
{{ $orig := resources.Get $rel }}
{{ if $orig }}
  {{ $thumb := $orig.Resize "400x q82" }}
  {{ $thumbWebp := $orig.Process "resize 400x webp q80" }}
  <a class="fav-card" href="{{ .RelPermalink }}">
    <picture class="fav-frame">
      <source type="image/webp" srcset="{{ $thumbWebp.RelPermalink }}">
      <img src="{{ $thumb.RelPermalink }}"
           width="{{ $thumb.Width }}" height="{{ $thumb.Height }}"
           alt="{{ .Params.alt | default "" }}"
           loading="lazy" decoding="async">
    </picture>
    <div class="fav-meta">
      <span class="fav-date smallcaps">{{ .Date.Format "2006 · 01" }}</span>
      <span class="fav-place">{{ with .Params.cities }}{{ index . 0 }}{{ end }}{{ with .Params.countries }}, {{ index . 0 }}{{ end }}</span>
    </div>
  </a>
{{ end }}
```

- [ ] **Step 2: Update `index.html` to use the partial and rename the CSS class**

Replace the entire contents of `themes/notebook/layouts/index.html` with:

```html
{{ define "main" }}
{{ $favs := where (where site.RegularPages "Section" "posts") "Params.tags" "intersect" (slice "favourite") }}
{{ $favs = $favs.ByWeight }}

<div class="section-head">
  <h2>A few favourites</h2>
  <span class="rule"></span>
  <span class="glyph">✦</span>
</div>

<div class="gallery-grid">
  {{ range first 8 $favs }}
    {{ partial "gallery-card.html" . }}
  {{ end }}
  <div class="fav-more">
    <a href="{{ "/tags/favourite/" | relURL }}">see all favourites →</a>
  </div>
</div>

<div class="section-head">
  <h2>Browse</h2>
  <span class="rule"></span>
  <span class="glyph">✦</span>
</div>

<ul class="browse">
  <li><a href="{{ "/posts/" | relURL }}"><span class="num tnum">01</span><span class="label">Latest posts</span><span class="count smallcaps">{{ len (where site.RegularPages "Section" "posts") }}</span></a></li>
  <li><a href="{{ "/years/" | relURL }}"><span class="num tnum">02</span><span class="label">By year</span><span class="count smallcaps">{{ len site.Taxonomies.years }}</span></a></li>
  <li><a href="{{ "/countries/" | relURL }}"><span class="num tnum">03</span><span class="label">By country</span><span class="count smallcaps">{{ len site.Taxonomies.countries }}</span></a></li>
  <li><a href="{{ "/cities/" | relURL }}"><span class="num tnum">04</span><span class="label">By city</span><span class="count smallcaps">{{ len site.Taxonomies.cities }}</span></a></li>
  <li><a href="{{ "/artists/" | relURL }}"><span class="num tnum">05</span><span class="label">By artist</span><span class="count smallcaps">{{ len site.Taxonomies.artists }} known</span></a></li>
  <li><a href="{{ "/tags/" | relURL }}"><span class="num tnum">06</span><span class="label">By tag</span><span class="count smallcaps">{{ len site.Taxonomies.tags }}</span></a></li>
</ul>
{{ end }}
```

- [ ] **Step 3: Rename `.favourites-grid` → `.gallery-grid` in CSS**

In `themes/notebook/assets/css/site.css`, make these two changes:

Line 191 — change:
```css
/* homepage — favourites grid */
.favourites-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: clamp(0.75rem, 1.5vw, 1.25rem); margin: 0.5rem 0 0.5rem; }
```
to:
```css
/* gallery grid (homepage, taxonomy, list pages) */
.gallery-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: clamp(0.75rem, 1.5vw, 1.25rem); margin: 0.5rem 0 0.5rem; }
```

Line 202 — change:
```css
  .favourites-grid { grid-template-columns: repeat(2, 1fr); }
```
to:
```css
  .gallery-grid { grid-template-columns: repeat(2, 1fr); }
```

- [ ] **Step 4: Verify in browser**

Run `make dev` (or confirm the already-running server picks up the changes). Open http://localhost:1313 and confirm:
- Homepage favourites grid looks identical to before
- No visual regressions on the browse section

- [ ] **Step 5: Commit**

```bash
git add themes/notebook/layouts/partials/gallery-card.html themes/notebook/layouts/index.html themes/notebook/assets/css/site.css
git commit -m "refactor(partial): extract gallery-card partial and rename grid CSS class"
```

---

### Task 2: Update `taxonomy.html` to use gallery grid

**Files:**
- Modify: `themes/notebook/layouts/_default/taxonomy.html`

- [ ] **Step 1: Replace the template**

Replace the entire contents of `themes/notebook/layouts/_default/taxonomy.html` with:

```html
{{ define "title" }}{{ .Title }} · {{ .Data.Plural | humanize }} · {{ site.Title }}{{ end }}

{{ define "main" }}
<section class="list-page taxonomy-page">
  <header class="section-head">
    <h2>{{ .Data.Singular | humanize }}: {{ .Title }}</h2>
    <span class="rule"></span>
    <span class="glyph">✦</span>
  </header>

  <p class="taxonomy-count smallcaps">{{ len .Pages }} {{ if eq (len .Pages) 1 }}photo{{ else }}photos{{ end }}</p>

  <div class="gallery-grid">
    {{ range .Pages.ByDate.Reverse }}
      {{ partial "gallery-card.html" . }}
    {{ end }}
  </div>
</section>
{{ end }}
```

- [ ] **Step 2: Verify in browser**

Open a taxonomy term page, e.g. http://localhost:1313/tags/favourite/ and http://localhost:1313/cities/london/. Confirm:
- Photos display in a 4-column square grid
- Most recent photo (by date taken) appears first
- Clicking a photo navigates to the post

- [ ] **Step 3: Commit**

```bash
git add themes/notebook/layouts/_default/taxonomy.html
git commit -m "feat(list): use gallery grid on taxonomy term pages"
```

---

### Task 3: Update `list.html` to use gallery grid and fix sort order

**Files:**
- Modify: `themes/notebook/layouts/_default/list.html`

- [ ] **Step 1: Replace the template**

Replace the entire contents of `themes/notebook/layouts/_default/list.html` with:

```html
{{ define "title" }}{{ .Title }} · {{ site.Title }}{{ end }}

{{ define "main" }}
<section class="list-page">
  <header class="section-head">
    <h2>{{ .Title }}</h2>
    <span class="rule"></span>
    <span class="glyph">✦</span>
  </header>

  {{ with .Content }}<div class="list-intro">{{ . }}</div>{{ end }}

  {{ $paginator := .Paginate (.Pages.ByDate.Reverse) }}
  <div class="gallery-grid">
    {{ range $paginator.Pages }}
      {{ partial "gallery-card.html" . }}
    {{ end }}
  </div>

  {{ template "_internal/pagination.html" . }}
</section>
{{ end }}
```

- [ ] **Step 2: Verify in browser**

Open http://localhost:1313/posts/. Confirm:
- Photos display in a 4-column square grid
- Most recent photo (by date taken, not publish date) appears first
- Pagination controls appear and work correctly

- [ ] **Step 3: Commit**

```bash
git add themes/notebook/layouts/_default/list.html
git commit -m "feat(list): use gallery grid on posts list, sort by date taken"
```

---

### Task 4: Delete `post-card.html` and remove dead card CSS

**Files:**
- Delete: `themes/notebook/layouts/partials/post-card.html`
- Modify: `themes/notebook/assets/css/site.css` (remove card rules)

- [ ] **Step 1: Delete `post-card.html`**

```bash
git rm themes/notebook/layouts/partials/post-card.html
```

- [ ] **Step 2: Remove dead card CSS from `site.css`**

In `themes/notebook/assets/css/site.css`, remove these lines (the "post cards" block and the `.cards` rule):

```css
/* post cards (list views) */
.card { display: grid; grid-template-columns: 6rem 1fr; gap: 1rem; padding: 0.9rem 0; border-bottom: 1px solid var(--rule); text-decoration: none; color: var(--ink); align-items: start; }
.card:hover .card-title, .card:hover .card-place { color: var(--coral); }
.card-thumb { aspect-ratio: 1 / 1; overflow: hidden; background: var(--bg-warm); }
.card-thumb img { width: 100%; height: 100%; object-fit: cover; }
.card-meta { display: flex; flex-direction: column; gap: 0.15rem; }
.card-date { font-size: 0.78rem; color: var(--muted); }
.card-place { font-style: italic; color: var(--ink-soft); }
.card-title { font-size: 1.05rem; }
```

Also remove the `.cards` rule in the list pages section:
```css
.cards { border-top: 1px solid var(--rule); }
```

- [ ] **Step 3: Run `make check` and verify**

```bash
make check
```

Expected: build succeeds, pa11y passes with 0 errors, htmltest shows no new errors beyond the known alt-text issues.

- [ ] **Step 4: Commit**

```bash
git add themes/notebook/assets/css/site.css
git commit -m "refactor(css): remove unused post-card partial and card CSS"
```
