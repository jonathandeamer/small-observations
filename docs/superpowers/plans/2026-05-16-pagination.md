# Pagination Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Hugo's built-in numbered pagination with a minimal `← older · page N of M · newer →` text-based partial.

**Architecture:** Create a custom `pagination.html` partial that reads `.Paginator` from the page context; update `list.html` to call it instead of the built-in template; add four CSS rules for the pagination bar.

**Tech Stack:** Hugo templates, hand-written CSS. No JS. No template test suite — verification is `make build` + browser inspection.

---

### Task 1: Create `pagination.html` partial and add CSS

**Files:**
- Create: `themes/notebook/layouts/partials/pagination.html`
- Modify: `themes/notebook/assets/css/site.css`

- [ ] **Step 1: Create the partial**

Create `themes/notebook/layouts/partials/pagination.html` with this exact content:

```html
{{ $p := .Paginator }}
{{ if gt $p.TotalPages 1 }}
<nav class="pagination" aria-label="Page navigation">
  {{ if $p.Prev }}
    <a href="{{ $p.Prev.URL }}">← newer</a>
  {{ else }}
    <span class="pagination-disabled">← newer</span>
  {{ end }}
  <span class="pagination-info">page {{ $p.PageNumber }} of {{ $p.TotalPages }}</span>
  {{ if $p.Next }}
    <a href="{{ $p.Next.URL }}">older →</a>
  {{ else }}
    <span class="pagination-disabled">older →</span>
  {{ end }}
</nav>
{{ end }}
```

- [ ] **Step 2: Add CSS**

In `themes/notebook/assets/css/site.css`, insert this block after the `/* list pages */` section (after line 165, before the `/* taxonomy pages */` comment):

```css
/* pagination */
.pagination { display: flex; justify-content: center; align-items: baseline; gap: 1rem; margin: 2rem 0 1rem; font-size: 0.88rem; }
.pagination a { color: var(--link); text-decoration: none; border-bottom: 1px solid var(--link); padding-bottom: 1px; }
.pagination-disabled { color: var(--muted); }
.pagination-info { color: var(--muted); }
```

- [ ] **Step 3: Verify build**

```bash
make build
```

Expected: builds cleanly, no errors.

- [ ] **Step 4: Commit**

```bash
git add themes/notebook/layouts/partials/pagination.html themes/notebook/assets/css/site.css
git commit -m "feat(partial): add minimal text-based pagination partial"
```

---

### Task 2: Wire `list.html` to use the new partial

**Files:**
- Modify: `themes/notebook/layouts/_default/list.html`

- [ ] **Step 1: Replace the built-in pagination call**

In `themes/notebook/layouts/_default/list.html`, find:

```html
  {{ template "_internal/pagination.html" . }}
```

Replace with:

```html
  {{ partial "pagination.html" . }}
```

- [ ] **Step 2: Verify build**

```bash
make build
```

Expected: builds cleanly, no errors.

- [ ] **Step 3: Verify in browser**

With a server running (`make dev`), open http://localhost:1313/posts/ and confirm:
- The numbered pagination is gone
- `← newer · page 1 of 6 · older →` appears at the bottom (← newer greyed out on page 1)
- Clicking `newer →` navigates to `/posts/page/2/`
- On page 2, both `← newer` and `older →` are active links
- On the last page, `older →` is greyed out

- [ ] **Step 4: Commit**

```bash
git add themes/notebook/layouts/_default/list.html
git commit -m "feat(list): use custom pagination partial"
```
