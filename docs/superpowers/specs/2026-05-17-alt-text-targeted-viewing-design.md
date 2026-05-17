# Alt Text Targeted Viewing Pass Design

## Context

The editorial pass landed at commit `182804c` and pushed the draft to roughly 80–85% quality. The scoped-viewing approach during that pass deliberately left value on the table: identifiable people, embedded text, and artist signatures cannot be reliably surfaced from text alone. A targeted full-viewing pass on the entries most likely to yield real corrections is the right cost/benefit point before alt text gets imported to post front matter.

## Goal

For each entry in `docs/alt-text-draft.md` that meets the viewing criterion, look at the image and update the caption to include any information that text-only review missed. Stay alt-only this pass — no front matter, no captions.

## What to look for when viewing

Apply in this order of priority:

1. **Identifiable people, characters, or figures.** Athletes, musicians, politicians, public figures, religious/cultural figures, fictional characters (Mr Monopoly, specific superheroes, specific Beatles, specific footballers). Only name when visually clear; do not infer from context.
2. **Complete embedded text.** Slogans, tags, dates, dedications, additional signs or words the existing caption summarises or omits. Quote verbatim in straight double quotes.
3. **Artist signatures.** Most street art is signed somewhere — corner, edge, on a tag. Include the signature as visible (e.g., `signed "@name"` or `signed "By Name"`).
4. **Substrate corrections.** "Utility box" / "telecoms cabinet" / "street box" / "ventilation grille" — fix where the existing word is wrong.
5. **Specific style descriptors** when identifiable (manga, comic-book panel, Lichtenstein-style, sticker-bombed, Keith Haring-style). Otherwise keep the generic stylised/comic-style/stencilled vocabulary from the editorial pass.

If viewing surfaces nothing new beyond the current caption, leave the entry unchanged.

## Scope

Apply the viewing criterion to every entry except those on the skip list below.

**Skip — already viewed in the editorial pass:**

- `assets/img/2016/05/2016-05-04-berlin.jpg`
- `assets/img/2016/09/2016-09-14-new-york.jpg`
- `assets/img/2017/08/2017-08-04-greater-london.jpg`
- `assets/img/2021/06/2021-06-28-greater-london.jpg`
- `assets/img/2022/04/2022-04-07-greater-london.jpg`
- `assets/img/2023/05/2023-05-05-liverpool.jpg`
- `assets/img/2024/01/2024-01-13-liverpool.jpg`
- `assets/img/2024/02/2024-02-25-barcelona.jpg`
- `assets/img/2025/05/2025-05-15-san-francisco.jpg`

**Skip — low-value (description is already complete and additional viewing is highly unlikely to yield improvement):**

- `assets/img/2015/10/2015-10-12-greater-london.jpg` — short stencil text already captured in full
- `assets/img/2016/11/2016-11-19-greater-london.jpg` — wall text already captured in full
- `assets/img/2022/03/2022-03-15-greater-london.jpg` — short stencil text already captured in full
- `assets/img/2022/09/2022-09-24-derbyshire-dales.jpg` — metal sculpture, no expected text or figure to identify
- `assets/img/2024/03/2024-03-16-leeds.jpg` — pure abstract pattern
- `assets/img/2025/07/2025-07-25-reykjavikurborg.jpg` — watermelon, no expected text or figure
- `assets/img/2025/07/2025-07-26-reykjavikurborg-2.jpg` — falcon head pattern, no expected text or figure
- `assets/img/2025/11/2025-11-03-chicago.jpg` — orange monster face, no expected text or figure
- `assets/img/2025/12/2025-12-04-greater-london.jpg` — brown bird, no expected text or figure
- `assets/img/2026/02/2026-02-17-greater-london.jpg` — frog on skull, no expected text or figure

Everything else (roughly 90 entries) is in scope for viewing. Most viewings will result in no caption change. The hit rate of useful corrections is expected to be 15–30% — high enough to justify the full pass, low enough that "no change" is the most common outcome.

## Workflow

Batched viewing is acceptable because path-to-caption pairing is now structurally preserved (the rewrite is in-place after the colon). Suggested batch size: 10–15 images per round.

For each batch:

1. Read the current entries for the batch (group by directory or by date range for sensible chunks).
2. Issue parallel `view_image` (Read tool, which handles JPEG) calls for all batch images.
3. For each image in the batch, decide:
   - **No change** if viewing surfaced nothing new
   - **Edit** if any of the five lookup items applies
4. Apply edits one per `Edit` call, using the entire current line as `old_string` and the updated line as `new_string`.
5. Move to the next batch.

Editorial criteria from `2026-05-17-alt-text-editorial-design.md` still apply:

- Lead with the artwork, substrate trails
- British English
- Target length 125–220 chars; allow longer for entries with substantial new text
- No "image of" / "photo of" prefixes
- Path string left of the colon is immutable

## Verification

After all batches:

- Line count unchanged.
- Path set unchanged vs `HEAD`.
- No duplicate paths.
- No US spellings (re-run the editorial-pass grep including `colorful`, `stylized`, `stenciled`, `ladybug`).
- Spot-check: any entry that now names a person, includes a signature, or quotes additional text should clearly improve on its previous version.

## Commit scope

Single commit. Only `docs/alt-text-draft.md`. Leave unrelated modified `content/posts/*.md` files unstaged.
