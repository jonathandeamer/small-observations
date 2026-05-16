# Alt Text Redo Design

## Context

The existing `docs/alt-text-draft.md` contains correct-looking image paths, but at least some captions are attached to the wrong image paths. A mechanical check confirmed path completeness and ordering, but that check could not validate whether each caption described its paired image.

The likely failure mode was batch processing: several images were viewed first, then captions were carried forward in conversation context and written later. That allowed caption-to-path alignment to drift while the final path list still remained complete and sorted.

## Goal

Replace `docs/alt-text-draft.md` with a corrected draft where each caption is generated and written atomically for the exact image path being viewed.

## Workflow

1. Use the sorted filesystem image list under `assets/img` as the only source of truth.
2. Overwrite `docs/alt-text-draft.md` with a short header.
3. For each image path, process one image at a time:
   - view the exact image file
   - draft one concise caption for that exact path
   - use filename/path context, such as date and location, when it helps disambiguate the scene
   - append that single path-and-caption line to `docs/alt-text-draft.md`
   - verify the last written line contains the same path before moving on
4. Avoid carrying multiple unwritten captions in memory.
5. Do not update post front matter during this pass.

The visible image remains the primary source for the caption. Filename context may inform wording such as city, country, or date, but should not override what is visibly present.

## Verification

After all images are processed:

- Count image files under `assets/img`.
- Count markdown entries in `docs/alt-text-draft.md`.
- Diff the sorted filesystem paths against the ordered paths extracted from the docs file.
- Check for duplicate paths.
- Spot-check any path/caption pairs flagged by the user as previously wrong.

## Commit Scope

Commit only the corrected `docs/alt-text-draft.md` after verification. Leave unrelated modified `content/posts/...` files untouched.
