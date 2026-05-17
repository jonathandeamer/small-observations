# Alt Text Editorial Pass Design

## Context

`docs/alt-text-draft.md` has been corrected for path-to-caption pairing and converted to British English. A subsequent review against accessibility best practices (W3C WAI, WebAIM, Cooper Hewitt Guidelines for Image Description) surfaced several systemic issues with the existing wording:

- Substrate (wall, box, structure) is front-loaded; the artwork itself appears second.
- Some descriptions contain inferred meaning, emotional projection, or photographer's context not visible in the image (e.g. "weary ape", "Brooklyn wall mural" where Brooklyn is not visible).
- Generic vocabulary ("cartoon", "cartoon-style") is repeated heavily where more specific terms (stencilled, line-drawn, stylised, comic-style, geometric, simplified) would serve better.
- Some identifiable people are described generically rather than named.
- Surroundings sometimes dominate the description when the artwork is the actual subject.

## Goal

Rewrite each line in `docs/alt-text-draft.md` in place against a fixed set of editorial criteria so the resulting alt text is more useful to a screen-reader user encountering the photo. Stay alt-only this pass — visible captions and front-matter integration are explicitly out of scope.

## Editorial criteria

Applied atomically per entry. Numbered for reference from the plan.

1. **Lead with the artwork's content.** Substrate (wall, box, fence, bridge, structure) is mentioned second, or omitted when not visually integral.
2. **Quote text in the image verbatim** using straight double quotes. Slogans, captions, signatures, dialogue.
3. **Name identifiable people, characters, and recognisable depicted things** where visually clear. Do not infer identity from filename, location, or photographer's knowledge. When in doubt, describe what is visible.
4. **Strip evaluative language.** "Powerful", "stunning", "beautiful", "striking" do not belong.
5. **Strip inferred meaning.** Do not state the artwork's intent, message, or political position unless the artwork literally depicts or names it. Quoted text in the artwork is allowed to carry meaning by itself.
6. **Vary the visual vocabulary.** Where appropriate, replace generic "cartoon" / "cartoon-style" with more specific terms: stencilled, line-drawn, stylised, comic-style, geometric, simplified, painted.
7. **British English throughout.** Colour, grey, coloured, organised. Re-verify after rewriting.
8. **Target length:** one to two sentences, roughly 125–220 characters. One sentence is the norm; allow longer only for genuinely complex scenes.
9. **No "image of" / "photo of" prefixes.** Screen readers already announce.
10. **Preserve correct path-to-caption pairing.** Path strings and ordering must not change; only the caption text after the colon is rewritten.

## Scoped viewing heuristic

Default: rewrite from the existing caption text alone. View the image only when the rewrite would assert something the existing caption does not.

Trigger viewing when any of the following is true for an entry:

- **Identifiable-person check.** The current caption uses generic terms ("portrait of a guitarist", "elderly man", "blonde face") and there is reason to suspect a named person (mural context, accompanying text, photographer's note).
- **Location/context-leak check.** The current caption names a place not in the filename and not obviously inside the image (e.g. "Brooklyn" when the path is `new-york`).
- **Interpretive-language verification.** The current caption ascribes emotion or activity ("weary", "smiling", "using naloxone to fight overdoses") and you want to keep or scrub it deliberately.
- **Substrate-vs-artwork ambiguity.** The current caption foregrounds the substrate so heavily that you cannot tell from text alone whether the substrate is visually integral or incidental.

Pre-identified viewing candidates from the review:

- `assets/img/2024/01/2024-01-13-liverpool.jpg` — confirm whether "Beatles-inspired scenes" includes an identifiable Beatles portrait.
- `assets/img/2017/08/2017-08-04-greater-london.jpg` — confirm the "portrait of a guitarist" is recognisable as Chuck Berry.
- `assets/img/2023/05/2023-05-05-liverpool.jpg` — confirm whether the "man's face held between two hands" is an identifiable person.
- `assets/img/2024/02/2024-02-25-barcelona.jpg` — confirm whether the "elderly bald man" portrait is an identifiable person.
- `assets/img/2016/09/2016-09-14-new-york.jpg` — confirm whether "Brooklyn" is visible in the image or carry-over context.
- `assets/img/2016/05/2016-05-04-berlin.jpg` — confirm "weary ape" is supported by the drawing's posture.
- `assets/img/2025/05/2025-05-15-san-francisco.jpg` — confirm whether the mural visibly depicts naloxone use vs that being external context.
- `assets/img/2021/06/2021-06-28-greater-london.jpg` — decide substrate-vs-artwork lead for the flamingo ventilation structure.
- `assets/img/2022/04/2022-04-07-greater-london.jpg` — decide substrate-vs-artwork lead for the flamingo under the bridge.

Other entries may surface viewing triggers during the pass; the heuristic above governs.

## Verification

After all entries are rewritten:

- Path-to-caption pairing intact (each line's path matches the same path in the previous version).
- Line count unchanged.
- No duplicate paths.
- No instance of "color", "gray", "favorite", "center", "organize" or other US spellings.
- Spot-check the pre-identified viewing candidates produced sensible outputs.

## Commit scope

Single commit. Only `docs/alt-text-draft.md`. Do not stage or touch unrelated modified files (the in-progress `content/posts/*.md` edits remain unstaged).
