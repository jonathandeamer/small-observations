# Tag Taxonomy Design

## Context

Posts have a `tags` taxonomy alongside `countries`, `cities`, `artists`, and `years`. The first four are well-bounded (one kind of thing each). `tags` is the catch-all axis and currently carries an inconsistent mix: subject categories (`bird`, `flamingo`), named individuals (`John Lennon`, `Kurt Cobain`), neighbourhoods (`Parkland Walk`, `Baltic Triangle`), events (`Liverpool Biennial`), brand/club identifiers (`Liverpool FC`, `Beatles`), and a few odd singletons. Casing, plurality, and singleton tolerance are uneven across the set.

Now that alt text has been human-reviewed and is treated as authoritative, the alt text plus body text can drive a consistent tag derivation. This design fixes the conventions and the derivation process; index-page presentation is deferred until the new tag set is real and visible.

## Goal

Establish a single, internally consistent design for the `tags` taxonomy that:

1. Aids navigation and discoverability for visitors browsing the archive.
2. Lets the front matter act as the quick-context layer for named entities not depicted in the photo (e.g. `John Lennon` on a "War is Over" piece).
3. Keeps the rules legible enough that a future post can be tagged consistently without consulting prior posts.

Front-matter-only this pass. No template work. No reorganisation into multiple taxonomies.

## Design decisions

### One taxonomy, four purposes

`tags` carries all of the following kinds of entry, mixed together in the same axis:

1. **Subjects** — what is depicted in the photo (people, characters, animals, objects, recurring motifs).
2. **Themes** — the cause or movement the artwork engages with (slogans, social/political/cultural register).
3. **Context** — named people, places, or events the artwork references but does not depict (`John Lennon` on a "War is Over" piece; `Burning Man` for a sculpture from that exhibition).
4. **Styles** — distinctive visual style or medium (`stencil`, `sticker`, `sculpture`, `Banksy-style`, `Lichtenstein-style`). Format words common to almost every post are excluded — see the floor.

A visitor lands on `/tags/<x>/` regardless of which purpose `<x>` serves; they receive a gallery of every post whose tag set includes that term.

### Singleton tolerance: liberal

Any meaningful term in a post is fair game as a tag, including those that appear in only one post today. The bar is "plausible future category": if the term could imaginably recur (another mural depicting the same person, another piece tagged with the same theme, another visit to the same event), tag it. This keeps the metadata rich and the tag page useful even when it returns a set of one.

The site is permitted to grow a long tail of singleton tags. The expectation is the eventual tag set sits somewhere between 150 and 250 distinct entries.

### Generic floor: do not tag

Words too generic to be useful filters are excluded even when they appear in alt text. The floor covers four categories:

- **Pure format** — `mural`, `painted`, `graffiti`, `wall`, `street art`. These apply to virtually every post.
- **Generic body parts** — `face`, `hand`, `eye`, `head`. Visually present in many posts; not what visitors search for.
- **Generic colours and shapes** — `blue`, `pink`, `circle`, `geometric`, `abstract` (as a colour-or-shape word alone).
- **Loose adjectives** — `bright`, `large`, `huge`, `small`, `colourful`.

Style-specific words clearly above the floor stay (`stencil`, `sticker`, `sculpture`, `Lichtenstein-style`, `Banksy-style`).

### Multi-level tagging

When a post supports both a generic and a more specific category, tag both. A visitor browsing `/tags/bird/` sees every bird; a visitor browsing `/tags/warbler/` sees only warblers. Both are valid browses; both should work.

Examples:

| Visible content | Tags |
|---|---|
| Mural with a warbler | `bird`, `warbler` |
| Mural depicting the Beatles together | `Beatles`, `John Lennon`, `Paul McCartney`, `George Harrison`, `Ringo Starr` |
| Mural of Robbie Fowler in a Liverpool kit | `football`, `footballer`, `Liverpool FC`, `Robbie Fowler` |
| Stencil of a hare among echinacea | `hare`, `flowers` (skip generic `wildlife`) |
| Memorial mural for George Floyd and Breonna Taylor | `memorial`, `Black Lives Matter`, `George Floyd`, `Breonna Taylor` |

The cost is that some posts carry six to eight tags. The benefit is multiple legitimate paths into the same content.

### Naming conventions

Front matter is the human-facing surface (tag chips on post pages, the index list, the URL slug derivation). Conventions:

| Tag kind | Convention | Examples |
|---|---|---|
| Common-noun subject | lowercase, singular | `bird`, `flamingo`, `skeleton`, `footballer`, `taco`, `vampire` |
| Proper noun (person, team, place, event) | title case, as the world spells it | `John Lennon`, `Liverpool FC`, `Burning Man`, `Chinatown`, `Halloween`, `Barbican` |
| Movement or slogan | verbatim casing | `Black Lives Matter`, `Marriage Equality`, `Slava Ukraini`, `Abolish ICE` |
| Style descriptor | lowercase or title case to match the style's own usage | `stencil`, `sticker`, `sculpture`, `Lichtenstein-style`, `Banksy-style` |
| Theme without a canonical name | lowercase | `climate`, `anti-war`, `housing`, `memorial`, `protest`, `music` |

Hugo slugifies these for URLs (`Black Lives Matter` → `/tags/black-lives-matter/`); the casing in front matter is for display. Pinned cases:

- `Beatles`, not `The Beatles`
- `Liverpool FC`, not `LFC`
- `stencil` (the noun), not `stencilled` (the verb)

### Deriving tags from a post

For each post, work through the alt text and any body text and assemble the tag set in this order:

1. **Subjects depicted.** Every named or recognisable thing in the artwork. Apply multi-level: generic plus specific where both are meaningful.
2. **Themes engaged.** Any cause, slogan, or movement language. Use the artwork's own wording verbatim when it appears in the image; otherwise the cleanest common name.
3. **Context references.** Named people, places, or events the artwork points at but does not depict; pull from body text as well as from artwork captions.
4. **Style.** Only when the style is distinctive and named (Lichtenstein, Banksy, comic, stencil, sculpture, etc.). Skip pure format words.
5. **Apply the floor.** Remove anything from the candidate set that matches the generic-floor categories.
6. **Apply naming conventions.** Normalise casing and plurality per the table.
7. **De-duplicate against existing tags** in the global set so casing/spelling stays consistent (e.g. `Chinatown` not `China town`; `Beatles` not `The Beatles`).

The output is the post's complete tag set.

## Out of scope (deferred)

- **Tag index page design.** With a liberal singleton policy the `/tags/` page will grow long; whether to keep plain alphabetical, add frequency bands, or do something else will be decided once the real tag set is in place and viewable.
- **Multi-taxonomy split.** Subjects/themes/styles will not be separated into their own Hugo taxonomies. If the volume eventually becomes unmanageable, that decision can be revisited.
- **Tag descriptions or `/tags/<x>/_index.md` pages.** No per-tag prose pages.
- **Hierarchical or nested tags.** Hugo's taxonomy system is flat; this design stays flat.

## Validation

After application across the existing 109 posts:

- Every tag in active use conforms to the naming conventions.
- No tag from the generic floor exists in the set.
- For each post where the alt text or body text supports both a generic and a specific category, both are present.
- The set of distinct tags grows from the current ~33 to something in the range of 150 to 250, with a long tail of singletons that look like categories someone could plausibly browse.
- `make build` and `make check` pass.
- A spot check of ten posts (a mix of complex and simple) shows the derivation procedure was applied consistently.

## Commit scope

This work touches `content/posts/*.md` front matter, plus a documentation addition to `CLAUDE.md` codifying the conventions. No template, CSS, or ingest changes.
