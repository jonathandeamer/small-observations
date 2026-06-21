# Small Observations — JSON-LD and Microformats2 Design Spec

**Date:** 2026-06-21
**Status:** Under Review

## Purpose

Add rich semantic metadata to the Hugo site to support modern web standards, search engines (Google Images), and IndieWeb clients. This mirrors the metadata work recently completed on the sister site (`~/homepage/`) but adapts the schema representations to fit a photo blog of street art rather than a personal profile page.

## Core Requirements

1.  **JSON-LD Structured Data**:
    *   **Homepage**: Emit a `schema.org/Blog` schema defining the site, its description, and its author.
    *   **Post Pages**: Emit a `schema.org/BlogPosting` schema that nests:
        *   An `ImageObject` representing the photo asset.
        *   A `Place` containing the city/country and geo-coordinates (from EXIF) if available.
        *   A `VisualArtwork` representing the depicted street art itself if an artist is tagged.
2.  **Microformats2 Integration**:
    *   Define the post container on single pages as an `h-entry`.
    *   Map existing HTML elements to Microformats2 class properties (`p-name`, `e-content`, `u-photo`, `u-featured`, `dt-published`, `dt-created`).
    *   Represent the post author as an invisible `h-card` referencing the canonical identity on `https://jonathandeamer.com` to maintain the existing page aesthetics.
3.  **Strict Constraints Check**:
    *   Keep HTML weight minimal (≤ 10kb target).
    *   Ensure all CSS/HTML matches the local, no-JS, serif-only design guidelines.

---

## 1. JSON-LD Implementation Details

We will create a single, clean partial at `themes/notebook/layouts/partials/head-jsonld.html` and call it within the `<head>` block of `themes/notebook/layouts/_default/baseof.html`.

### Homepage Schema (`Blog`)

On the homepage (`.IsHome`), the partial will render:

```json
{
  "@context": "https://schema.org",
  "@type": "Blog",
  "name": "Small Observations",
  "description": "A notebook of street art I've enjoyed and photographed since 2005, browsable by city, artist, year, and tag.",
  "url": "https://smallobservations.net/",
  "author": {
    "@type": "Person",
    "name": "Jonathan Deamer",
    "url": "https://jonathandeamer.com"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Small Observations",
    "logo": {
      "@type": "ImageObject",
      "url": "https://smallobservations.net/apple-touch-icon.png"
    }
  }
}
```

### Post Page Schema (`BlogPosting`)

On individual posts (`.IsPage` / `.Kind "page"`), the partial will dynamically assemble a `BlogPosting`:

*   **Headline**: If `.Params.headline` exists, use it. Otherwise, generate a fallback (e.g. `"Photo taken in Paris on 14 July 2018"` or `"Photo taken 14 July 2018"`).
*   **Image**: Fetch the original photo, resize to the `1600px` edge (standard maximum width for the site), and extract width, height, and permalink. Wrap this in an `ImageObject` with the `alt` parameter as the `caption`.
*   **Place**: If `cities` or `countries` taxonomies exist, build a string (e.g., `"Paris, France"`). If GPS coordinates (`exif.lat`, `exif.lon`) are present in front matter, nest a `GeoCoordinates` object.
*   **VisualArtwork** (nested under `about`): If `.Params.artists` is populated, represent the artwork itself with the artists mapped to the `creator` field.

#### Blueprint of the Hugo template logic:

```html
{{ if .IsPage }}
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

---

## 2. Microformats2 Integration Details

All Microformats2 properties will be embedded using class annotations on existing semantic elements.

### Layout File Modifications

1.  **`themes/notebook/layouts/_default/single.html`**:
    *   Change `<article class="post">` to `<article class="post h-entry">`.
    *   In the title conditional, add `p-name` class:
        ```html
        {{ if .Params.headline }}
          <h1 class="post-title p-name">{{ .Params.headline }}</h1>
        {{ else if .Title }}
          <h1 class="post-title sr-only p-name">{{ .Title }}</h1>
        {{ end }}
        ```
    *   In the content block, add `e-content` class:
        ```html
        <div class="post-body e-content">
        ```
    *   In the colophon block, add `dt-published` class to the time:
        ```html
        Posted <time datetime="{{ .PublishDate.Format "2006-01-02" }}" class="tnum dt-published">{{ .PublishDate.Format "January 2006" }}</time>.
        ```
    *   Add an invisible author relation link inside the article tag to declare the author without changing the visual layout:
        ```html
        <link rel="author" class="p-author h-card" href="https://jonathandeamer.com" title="Jonathan Deamer">
        ```

2.  **`themes/notebook/layouts/partials/photo.html`**:
    *   In the fallback `<img>` element rendering, add `class="u-photo u-featured"`:
        ```html
        <img class="u-photo u-featured" src="{{ $jpeg1000.RelPermalink }}" ...>
        ```

3.  **`themes/notebook/layouts/partials/post-meta.html`**:
    *   Mark the photo's taken date as `dt-created` to provide chronological context to IndieWeb readers:
        ```html
        <time datetime="{{ .Date.Format "2006-01-02" }}" class="tnum dt-created">
        ```

---

## 3. Constraints Checklist & Verification Plan

### Page Weight Verification
*   We must audit a compiled single post HTML page to verify the total page weight does not exceed the `10kb` limit.
*   We must run HTML validation checks via `make check` to ensure neither the JSON-LD script blocks nor the new Microformat classes break HTML compliance.

### Commits Scope
*   **Commit Message format**: `feat(partial): add json-ld and h-entry microformats`
