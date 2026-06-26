# JSON-LD and Microformats2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add compliant JSON-LD structured data and Microformats2 tags to the Hugo site to support modern search indexing (Google Images) and IndieWeb clients without altering the existing visual design or breaking the 10kb HTML page-weight budget.

**Architecture:** We will implement JSON-LD via a dedicated layout partial `head-jsonld.html` wired into `<head>`. Microformats2 will be added via class decorators in the layout templates `single.html`, `photo.html`, and `post-meta.html`, representing the post author via an invisible `h-card` relationship link.

**Tech Stack:** Hugo templating, JSON-LD (Schema.org Blog, BlogPosting, Place, GeoCoordinates, VisualArtwork, ImageObject), Microformats2 (h-entry, h-card).

---

### Task 1: Create JSON-LD Layout Template Partial

**Files:**
- Create: `themes/notebook/layouts/partials/head-jsonld.html`

- [ ] **Step 1: Write the template partial code**
  Create the file `themes/notebook/layouts/partials/head-jsonld.html` and populate it with the complete Hugo/JSON-LD serialization logic:

  ```html
  {{ if .IsHome }}
    {{ $author := dict "@type" "Person" "name" "Jonathan Deamer" "url" "https://jonathandeamer.com" }}
    {{ $publisher := dict "@type" "Organization" "name" "Small Observations" "logo" (dict "@type" "ImageObject" "url" (absURL "/apple-touch-icon.png")) }}
    {{ $blog := dict "@context" "https://schema.org" "@type" "Blog" "name" "Small Observations" "description" (.Description | default site.Params.description) "url" site.BaseURL "author" $author "publisher" $publisher }}
    <script type="application/ld+json">{{ $blog | jsonify (dict "indent" "  ") | safeJS }}</script>
  {{ else if .IsPage }}
    {{ $author := dict "@type" "Person" "name" "Jonathan Deamer" "url" "https://jonathandeamer.com" }}
    {{ $publisher := dict "@type" "Organization" "name" "Small Observations" "logo" (dict "@type" "ImageObject" "url" (absURL "/apple-touch-icon.png")) }}
    
    {{/* 1. Image Object */}}
    {{ $imageObj := "" }}
    {{ $rel := printf "img/%s" .Params.photo }}
    {{ $orig := resources.Get $rel }}
    {{ if $orig }}
      {{ $img := $orig.Resize "1600x q82" }}
      {{ $imageObj = dict "@type" "ImageObject" "contentUrl" $img.Permalink "url" $img.Permalink "width" (printf "%d" $img.Width) "height" (printf "%d" $img.Height) "caption" (.Params.alt | default "") }}
    {{ end }}

    {{/* 2. Place / Location */}}
    {{ $place := "" }}
    {{ if or .Params.cities .Params.countries }}
      {{ $placeName := "" }}
      {{ with .Params.cities }}{{ $placeName = index . 0 }}{{ end }}
      {{ with .Params.countries }}{{ if $placeName }}{{ $placeName = printf "%s, %s" $placeName (index . 0) }}{{ else }}{{ $placeName = index . 0 }}{{ end }}{{ end }}
      
      {{ $geo := "" }}
      {{ if and .Params.exif.lat .Params.exif.lon }}
        {{ $geo = dict "@type" "GeoCoordinates" "latitude" .Params.exif.lat "longitude" .Params.exif.lon }}
      {{ end }}
      
      {{ $place = dict "@type" "Place" "name" $placeName }}
      {{ if $geo }}
        {{ $place = merge $place (dict "geo" $geo) }}
      {{ end }}
    {{ end }}

    {{/* 3. VisualArtwork */}}
    {{ $artwork := "" }}
    {{ if gt (len .Params.artists) 0 }}
      {{ $artists := slice }}
      {{ range .Params.artists }}
        {{ $artists = $artists | append (dict "@type" "Person" "name" .) }}
      {{ end }}
      {{ $artwork = dict "@type" "VisualArtwork" "name" (or .Params.headline .Title) "creator" $artists }}
      {{ if $place }}
        {{ $artwork = merge $artwork (dict "locationCreated" $place) }}
      {{ end }}
      {{ if $imageObj }}
        {{ $artwork = merge $artwork (dict "image" $imageObj.contentUrl) }}
      {{ end }}
    {{ end }}

    {{/* 4. Fallback Headline */}}
    {{ $headline := .Params.headline }}
    {{ if not $headline }}
      {{ $dateStr := .Date.Format "2 January 2006" }}
      {{ $placeStr := "" }}
      {{ with .Params.cities }}{{ $placeStr = index . 0 }}{{ end }}
      {{ $headline = printf "Photo taken %s" $dateStr }}
      {{ if $placeStr }}
        {{ $headline = printf "Photo taken in %s on %s" $placeStr $dateStr }}
      {{ end }}
    {{ end }}

    {{/* 5. Assemble Posting */}}
    {{ $post := dict "@context" "https://schema.org" "@type" "BlogPosting" "headline" $headline "datePublished" (.PublishDate.Format "2006-01-02T15:04:05Z") "dateCreated" (.Date.Format "2006-01-02T15:04:05Z") "author" $author "publisher" $publisher }}
    {{ if $imageObj }}
      {{ $post = merge $post (dict "image" $imageObj.contentUrl) }}
    {{ end }}
    {{ if $place }}
      {{ $post = merge $post (dict "spatialCoverage" $place) }}
    {{ end }}
    {{ if $artwork }}
      {{ $post = merge $post (dict "about" $artwork) }}
    {{ end }}
    
    <script type="application/ld+json">{{ $post | jsonify (dict "indent" "  ") | safeJS }}</script>
  {{ end }}
  ```

- [ ] **Step 2: Commit template**
  Commit the newly created template:
  ```bash
  git add themes/notebook/layouts/partials/head-jsonld.html
  git commit -m "feat(partial): create head-jsonld structured data partial"
  ```

---

### Task 2: Wire the JSON-LD partial into baseof.html

**Files:**
- Modify: `themes/notebook/layouts/_default/baseof.html`

- [ ] **Step 1: Edit baseof.html**
  Inject the newly created partial in `themes/notebook/layouts/_default/baseof.html` under the `<head>` section near `head-og.html`:

  ```html
    {{ partial "head-og.html" . }}

    {{ partial "head-jsonld.html" . }}

    <link rel="canonical" href="{{ .Permalink }}">
  ```

- [ ] **Step 2: Compile the site and verify homepage JSON-LD**
  Run: `make build`
  Verify that `public/index.html` contains the `Blog` schema:
  Run: `grep -A 10 "application/ld+json" public/index.html`
  Expected: Outputs the script tag containing the `@type: Blog` properties.

- [ ] **Step 3: Verify post JSON-LD (without artwork)**
  Verify `public/2016/09/new-york-brooklyn-squirrel/index.html` (which has no artist) contains the `BlogPosting` and `Place` details but no `VisualArtwork` (`about`) details:
  Run: `grep -A 25 "application/ld+json" public/2016/09/new-york-brooklyn-squirrel/index.html`
  Expected: JSON-LD block with `"@type": "BlogPosting"`, geo-coordinates `40.7078` and `-73.922`, but no `about` property.

- [ ] **Step 4: Verify post JSON-LD (with artwork)**
  Verify `public/2022/04/london-frankie-strand-pink-flamingo/index.html` (which has an artist) contains the `about` property mapping the `VisualArtwork` schema:
  Run: `grep -A 40 "about" public/2022/04/london-frankie-strand-pink-flamingo/index.html`
  Expected: Contains `"@type": "VisualArtwork"`, `"creator": [ { "@type": "Person", "name": "Frankie Strand" } ]`.

- [ ] **Step 5: Commit changes**
  ```bash
  git add themes/notebook/layouts/_default/baseof.html
  git commit -m "feat(home): wire head-jsonld partial into baseof.html"
  ```

---

### Task 3: Add Microformats2 to single.html layout

**Files:**
- Modify: `themes/notebook/layouts/_default/single.html`

- [ ] **Step 1: Annotate single.html with Microformats classes**
  Modify `themes/notebook/layouts/_default/single.html` to add the `h-entry`, `p-name`, `e-content`, `dt-published` classes, and the invisible author link:

  ```html
  {{ define "main" }}
  <article class="post h-entry">
    {{ partial "photo.html" (dict "page" . "eager" true) }}

    {{ if .Params.headline }}
      <h1 class="post-title p-name">{{ .Params.headline }}</h1>
    {{ else if .Title }}
      <h1 class="post-title sr-only p-name">{{ .Title }}</h1>
    {{ end }}

    {{ with .Content }}
    <div class="post-body e-content">
      {{ . }}
    </div>
    {{ end }}

    {{ partial "post-meta.html" . }}

    <p class="post-colophon">
      Posted <time datetime="{{ .PublishDate.Format "2006-01-02" }}" class="tnum dt-published">{{ .PublishDate.Format "January 2006" }}</time>.
      <a href="{{ "/posts/" | relURL }}">← all posts</a>
    </p>
    <link rel="author" class="p-author h-card" href="https://jonathandeamer.com" title="Jonathan Deamer">
  </article>
  {{ end }}
  ```

- [ ] **Step 2: Commit layout change**
  ```bash
  git add themes/notebook/layouts/_default/single.html
  git commit -m "feat(post): add h-entry and invisible author h-card to single.html"
  ```

---

### Task 4: Add Microformats2 classes to photo and post-meta partials

**Files:**
- Modify: `themes/notebook/layouts/partials/photo.html`
- Modify: `themes/notebook/layouts/partials/post-meta.html`

- [ ] **Step 1: Add u-photo classes in photo.html**
  Modify `themes/notebook/layouts/partials/photo.html` to annotate the `<img>` tag:

  ```html
    <img class="u-photo u-featured" src="{{ $jpeg1000.RelPermalink }}"
         srcset="{{ $jpeg600.RelPermalink }} 600w, {{ $jpeg1000.RelPermalink }} 1000w, {{ $jpeg1600.RelPermalink }} 1600w"
         sizes="(max-width: 700px) 100vw, 700px"
         width="{{ $jpeg1600.Width }}" height="{{ $jpeg1600.Height }}"
         alt="{{ $page.Params.alt | default "" }}"
         loading="{{ if $eager }}eager{{ else }}lazy{{ end }}"
         decoding="async">
  ```

- [ ] **Step 2: Add dt-created to post-meta.html**
  Modify `themes/notebook/layouts/partials/post-meta.html` to mark the photo taken date as `dt-created`:

  ```html
    <div class="row">
      <dt>Taken</dt>
      <dd>
        <time datetime="{{ .Date.Format "2006-01-02" }}" class="tnum dt-created">
          {{ .Date.Format "January " }}{{ with index $yearTerms 0 }}<a href="{{ .RelPermalink }}">{{ .LinkTitle }}</a>{{ else }}{{ $page.Date.Format "2006" }}{{ end }}
        </time>
      </dd>
    </div>
  ```

- [ ] **Step 3: Commit partial changes**
  ```bash
  git add themes/notebook/layouts/partials/photo.html themes/notebook/layouts/partials/post-meta.html
  git commit -m "feat(partial): add u-photo and dt-created classes to photo and metadata templates"
  ```

---

### Task 5: Verify Integration & Constraints

- [ ] **Step 1: Build the site and run checks**
  Run: `make build` and then `make check`
  Expected: Clean build, check audits pass (no HTML validation or format warning regressions).

- [ ] **Step 2: Verify HTML Microformats class strings are present in output**
  Run: `grep -i "h-entry" public/2016/09/new-york-brooklyn-squirrel/index.html`
  Expected: `<article class="post h-entry">`
  Run: `grep -i "u-photo u-featured" public/2016/09/new-york-brooklyn-squirrel/index.html`
  Expected: Matches the `<img>` tag.
  Run: `grep -i "dt-published" public/2016/09/new-york-brooklyn-squirrel/index.html`
  Expected: Contains `<time datetime="2026-05-15" class="tnum dt-published">May 2026</time>` (or correct format).
  Run: `grep -i "dt-created" public/2016/09/new-york-brooklyn-squirrel/index.html`
  Expected: Contains `<time datetime="2016-09-14" class="tnum dt-created">` (or correct format).
  Run: `grep -i "p-author" public/2016/09/new-york-brooklyn-squirrel/index.html`
  Expected: `<link rel="author" class="p-author h-card" href="https://jonathandeamer.com" title="Jonathan Deamer">`

- [ ] **Step 3: Verify output page weight limit**
  Check the HTML file size of a typical post page:
  Run: `wc -c public/2016/09/new-york-brooklyn-squirrel/index.html`
  Expected: Output size in bytes is strictly less than 10240 bytes (`10kb`).
