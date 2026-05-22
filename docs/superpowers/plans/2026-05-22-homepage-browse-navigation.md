# Homepage Browse Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move homepage archive navigation into a compact masthead-adjacent row and replace the long browse list with a short tags-and-cities explore section.

**Architecture:** The top router lives in the masthead partial so it sits directly under the tagline on the homepage. The homepage template generates the favourites gallery and then a small explore section from Hugo taxonomy data. Styling stays in the existing single CSS file with mobile wrapping as the primary constraint.

**Tech Stack:** Hugo templates, Hugo taxonomy collections, hand-written CSS, Makefile build verification.

---

### Task 1: Add Masthead Router

**Files:**
- Modify: `themes/notebook/layouts/partials/masthead.html`
- Modify: `themes/notebook/assets/css/site.css`

- [ ] **Step 1: Add homepage-only nav markup under the tagline**

In `themes/notebook/layouts/partials/masthead.html`, add a conditional nav after the tagline:

```go-html-template
  {{ if .IsHome }}
    <nav class="masthead-browse" aria-label="Browse the archive">
      <a href="{{ "/posts/" | relURL }}">latest</a>
      <span aria-hidden="true">·</span>
      <a href="{{ "/tags/favourite/" | relURL }}">favourites</a>
      <span aria-hidden="true">·</span>
      <a href="{{ "/tags/" | relURL }}">tags</a>
      <span aria-hidden="true">·</span>
      <a href="{{ "/cities/" | relURL }}">cities</a>
      <span aria-hidden="true">·</span>
      <a href="{{ "/years/" | relURL }}">years</a>
      <span aria-hidden="true">·</span>
      <a href="{{ "/countries/" | relURL }}">countries</a>
      <span aria-hidden="true">·</span>
      <a href="{{ "/artists/" | relURL }}">artists</a>
    </nav>
  {{ end }}
```

- [ ] **Step 2: Add compact wrapping nav CSS**

In `themes/notebook/assets/css/site.css`, add masthead nav styles near the existing masthead rules:

```css
.masthead-browse {
  margin: 0.45rem 0 0 0.15rem;
  display: flex;
  flex-wrap: wrap;
  column-gap: 0.42rem;
  row-gap: 0.18rem;
  align-items: baseline;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.08em;
  font-size: 0.9rem;
  color: var(--muted);
}
.masthead-browse a {
  color: var(--ink-soft);
  text-decoration: none;
  border-bottom: 1px solid var(--rule);
}
.masthead-browse a:hover {
  color: var(--coral);
  border-color: var(--coral);
}
.masthead-browse span { color: var(--coral); }
```

### Task 2: Replace Lower Browse List With Explore Section

**Files:**
- Modify: `themes/notebook/layouts/index.html`
- Modify: `themes/notebook/assets/css/site.css`

- [ ] **Step 1: Replace the existing Browse section**

In `themes/notebook/layouts/index.html`, remove the `Browse` section heading and `<ul class="browse">`. Add an `Explore` section after the favourites gallery:

```go-html-template
<div class="section-head">
  <h2>Explore</h2>
  <span class="rule"></span>
  <span class="glyph">✦</span>
</div>

<div class="home-explore" aria-label="Explore tags and cities">
  <p>
    <span class="home-explore-label smallcaps">tags</span>
    {{ $shownTags := 0 }}
    {{ range site.Taxonomies.tags.ByCount }}
      {{ if and (ne .Page.Title "favourite") (lt $shownTags 6) }}
        {{ if gt $shownTags 0 }}<span aria-hidden="true">·</span>{{ end }}
        <a href="{{ .Page.RelPermalink }}">{{ .Page.Title }}</a>
        {{ $shownTags = add $shownTags 1 }}
      {{ end }}
    {{ end }}
    <span aria-hidden="true">·</span>
    <a href="{{ "/tags/" | relURL }}">more tags</a>
  </p>

  <p>
    <span class="home-explore-label smallcaps">cities</span>
    {{ range $index, $term := first 6 site.Taxonomies.cities.ByCount }}
      {{ if gt $index 0 }}<span aria-hidden="true">·</span>{{ end }}
      <a href="{{ $term.Page.RelPermalink }}">{{ $term.Page.Title }}</a>
    {{ end }}
    <span aria-hidden="true">·</span>
    <a href="{{ "/cities/" | relURL }}">more cities</a>
  </p>
</div>
```

- [ ] **Step 2: Add explore CSS and retire old browse CSS**

In `themes/notebook/assets/css/site.css`, replace the `.browse` rules with:

```css
/* homepage — explore links */
.home-explore {
  max-width: var(--measure);
  margin: 0;
  color: var(--ink-soft);
}
.home-explore p {
  margin: 0;
  padding: 0.65rem 0.25rem;
  border-top: 1px solid var(--rule);
}
.home-explore p:last-child { border-bottom: 1px solid var(--rule); }
.home-explore-label {
  display: inline-block;
  min-width: 4.8rem;
  color: var(--muted);
  font-size: 0.82rem;
}
.home-explore a {
  color: var(--ink);
  text-decoration: none;
  border-bottom: 1px solid var(--rule);
}
.home-explore a:hover {
  color: var(--coral);
  border-color: var(--coral);
}
.home-explore span[aria-hidden="true"] {
  margin: 0 0.3rem;
  color: var(--coral);
}
```

Also remove the obsolete `.browse` mobile rules under `@media (max-width: 760px)` and `@media (max-width: 380px)`.

### Task 3: Local Scratch Hygiene

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Ignore visual companion scratch output**

Add this to `.gitignore` under scratch / throwaway work:

```gitignore
.superpowers/
```

### Task 4: Verification

**Files:**
- No source edits.

- [ ] **Step 1: Build outside the sandbox**

Run:

```bash
make build
```

Expected: Hugo build exits 0.

- [ ] **Step 2: Inspect rendered homepage HTML**

Run:

```bash
rg -n "masthead-browse|home-explore|favourite" public/index.html
```

Expected:

- `masthead-browse` appears once.
- `home-explore` appears once.
- `favourite` appears in the masthead/favourites gallery area, but not inside the `home-explore` tags row.

- [ ] **Step 3: Review diff and commit**

Run:

```bash
git diff --stat
git diff -- themes/notebook/layouts/partials/masthead.html themes/notebook/layouts/index.html themes/notebook/assets/css/site.css .gitignore
```

Commit with:

```bash
git add .gitignore themes/notebook/layouts/partials/masthead.html themes/notebook/layouts/index.html themes/notebook/assets/css/site.css docs/superpowers/plans/2026-05-22-homepage-browse-navigation.md
git commit -m "feat(home): surface browse links near masthead"
```
