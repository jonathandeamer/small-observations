# Photo-Post Descriptions Amendment

## Supersedes

This amends [`2026-05-17-titles-descriptions-design.md`](2026-05-17-titles-descriptions-design.md) for the **photo-post `title:` and `description:` fields only**. Everything else in the prior spec stands unchanged: source discipline, voice, term-page descriptions, index-page descriptions, headline rules, templates, anti-hallucination protocol, verification.

## Motivation

The prior spec was executed across all 109 photo posts. Reviewing the result in real share contexts — Google snippets, Twitter/Slack/Discord OG cards, RSS readers — surfaced one consistent problem:

**Title and description read as restatements of each other.** Example:

> **Title:** Kurt Cobain stencil, Seville
> **Description:** Photo of a blue stencil portrait of Kurt Cobain on a white wall covered in graffiti and tags, in Seville.

Both phrases answer the same question ("what's in the photo, where?"). In an OG card the image is already showing the viewer the answer, the title is already naming it, and the description burns its snippet length restating it. The description is not earning its place.

Three contributing patterns, present in roughly every post:

1. **`"Photo of a/an"` prefix** — adds no information in any surface where descriptions are seen (search snippets, social cards with image, RSS items). ~10 chars of dead weight per post.
2. **Trailing `", in <City>"`** — almost always already in the title.
3. **Near-verbatim alt restatement** — describes the image *next to the image*, leaving no room for any detail that adds value.

## Goal

Make the description carry information the title doesn't. Eliminating duplication is the central success criterion; form-word variance and year inclusion are the tools.

## Source discipline (unchanged)

Every claim must be citable to the post's own front matter or body. Permitted sources, voice rules, and forbidden moves are unchanged from the prior spec, sections "Source discipline" and "Voice". A new description that invents context (commissioning body, historical event, attribution not in alt/body/tags) is wrong even if it differentiates well. Fix the front matter first, then write the description.

## Revised description shape

```
<Form noun phrase> [+ one distinguishing detail not in title] [+ context]. <Year>.
```

### Form noun phrase

Replaces the universal `"Photo of"` prefix. Drawn from alt text — if alt calls it a stencil, the description leads with stencil. Preferred vocabulary, in rough order of frequency for this archive:

mural, stencil, sticker, sculpture, installation, painting, portrait, figure, scene, sign.

`"Photo of…"` remains the fallback when no form word fits (food, signage, ambient scenes). The bar: the form word must be defensible against alt text. If you can't underline the word in the alt, don't use it.

### Distinguishing detail

One short clause carrying something the title doesn't already have. Pick from, in order of preference:

1. **Context already in front matter** — artist signature mentioned in alt, commissioning body in body text, named project in `tags:`. Highest value because it tells the reader something the photo can't.
2. **A visual detail** the title omits — colour, material, surroundings, composition. Use only when no front-matter context is available.

Never include both — pick one. Both descend into restatement.

### Year

From `date.year` (equivalent to `years[0]`). Default placement: trailing as a standalone sentence (`". 2018."`). Weave into the sentence only when it reads naturally and stays grounded.

Year is mandatory. It is the single most reliable way to add information the title lacks and the image can't convey.

### City

Drop the trailing `", in <City>"` when the title already contains the city (which is nearly always). Keep city in the description only when the description is adding a neighbourhood, landmark, or street-level detail worth carrying ("on Golden Lane, London"). Even then, prefer to keep that detail in the title where it improves the title too.

### Length

Soft target 100–140 chars. Hard ceiling 160. (Was 100–120 / 140 in the prior spec; loosened to make room for the form word and year.)

## Title cleanup criteria

Titles are mostly already well-formed. The sweep touches a title only when it hits one of:

1. **Ends in a neighbourhood instead of a city** (e.g. `"…, Clarion Alley"` should be `"…, Clarion Alley, San Francisco"` or fold the neighbourhood into the subject).
2. **Duplicates the city inside the subject** (`"Mr. Monopoly beside New York landmarks, New York"` → drop the redundancy).
3. **Stacks three+ commas** in a way that reads heavily (consider folding neighbourhood detail out, or reordering).

No general title rewrite. The `<visual subject>, <City>` shape from the prior spec is correct.

## Worked examples

Showing title (unchanged unless flagged), prior description, new description, and the source field for each substantive claim in the new description.

### 1. Kurt Cobain stencil

- **Title:** Kurt Cobain stencil, Seville *(unchanged)*
- **Prior description:** Photo of a blue stencil portrait of Kurt Cobain on a white wall covered in graffiti and tags, in Seville.
- **New description:** Blue stencil on a tag-covered white wall. 2005.
- **Sources:** "stencil" ← alt + title; "blue" ← alt; "tag-covered white wall" ← alt; "2005" ← `date.year`.

### 2. Marriage equality mural

- **Title:** Marriage equality mural on a pub window, Dublin *(unchanged)*
- **Prior description:** Photo of a comic-style "YES" marriage equality mural painted on a pub window, signed Niall O'Lochlainn, in Dublin.
- **New description:** Comic-style mural signed Niall O'Lochlainn. 2016.
- **Sources:** "Comic-style mural" ← alt + `tags`; "signed Niall O'Lochlainn" ← alt; "2016" ← `date.year`. ("Pub window" deliberately omitted — already in the title.)

### 3. Hella Resist figure

- **Title:** "Hella Resist" figure beside Clarion street sign, San Francisco *(unchanged)*
- **Prior description:** Photo of a blue stylised figure in a yellow "Hella Resist" shirt painted on a corner beside a Clarion street sign in San Francisco.
- **New description:** Part of the Clarion Alley Mural Project: stylised blue figure in a yellow shirt. 2018.
- **Sources:** "Clarion Alley Mural Project" ← `tags`; "stylised blue figure in a yellow shirt" ← alt; "2018" ← `date.year`.

## Process

1. **Spec written and committed** (this document).
2. **Pilot rewrite:** select 10 posts spanning eras, places, and content types (street art, food, signs, sculpture, etc.). Draft new title+description for each, with source-field annotations as in the worked examples. Present diff for review.
3. **Refine spec** based on what feels off in the pilot. Update this document with any rule changes.
4. **Sweep:** rewrite descriptions for the remaining ~100 posts. Apply title cleanup only where a title hits one of the three criteria above.
5. **Commit in batches by year** so review stays tractable.
6. **Run `make check`** after each batch; verify the build succeeds and pa11y/htmltest/xmllint/vnu all pass.

## Verification (additive to the prior spec)

In addition to the prior spec's verification rules:

1. No description begins with `"Photo of"` unless no form word in the preferred vocabulary fits the alt.
2. No description ends with `", in <City>."` when the city is already in the title.
3. Every description contains the year, either trailing or woven.
4. Every description is ≤160 characters.
5. Spot-check: pick 10 posts at random and confirm that the title and description, read together as they would appear in a Slack/Twitter share card, are not restatements of each other.

## Out of scope

Term-page descriptions, index-page descriptions, headlines, templates, the `description`-vs-body-text relationship, and the overall site voice — all governed by the prior spec.
