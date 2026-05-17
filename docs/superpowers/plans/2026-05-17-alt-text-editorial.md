# Alt Text Editorial Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite each entry in `docs/alt-text-draft.md` so the caption text after the colon follows the editorial criteria from `docs/superpowers/specs/2026-05-17-alt-text-editorial-design.md`, without changing any path or the file's line ordering.

**Architecture:** In-place per-entry rewrite. For each line, decide from the current caption text whether viewing the image is needed (per the heuristic in the design doc). Apply the editorial criteria. Replace the caption portion only. Verify path-to-caption pairing after each replacement.

**Tech Stack:** Markdown, local filesystem, `view_image`, `Edit` (exact string replacement), `rg`, `sed`, `diff`, `git`.

---

## Task 1: Load Editorial Criteria Into Working Context

**Files:**
- Read: `docs/superpowers/specs/2026-05-17-alt-text-editorial-design.md`
- Read: `docs/alt-text-draft.md`

- [ ] **Step 1: Read the design doc end-to-end**

The ten editorial criteria and the scoped viewing heuristic must be in context for the entire rewrite. Re-reading mid-pass is fine; missing a criterion is not.

- [ ] **Step 2: Read the current draft end-to-end**

Get the full list of entries. Note the file structure: a short header, then one bullet line per image, each in the form `` - `assets/img/...`: caption text ``.

- [ ] **Step 3: Confirm the pre-identified viewing candidates exist in the current draft**

Run:

```bash
grep -c '^- `assets/img/2024/01/2024-01-13-liverpool\.jpg`' docs/alt-text-draft.md
grep -c '^- `assets/img/2017/08/2017-08-04-greater-london\.jpg`' docs/alt-text-draft.md
grep -c '^- `assets/img/2023/05/2023-05-05-liverpool\.jpg`' docs/alt-text-draft.md
grep -c '^- `assets/img/2024/02/2024-02-25-barcelona\.jpg`' docs/alt-text-draft.md
grep -c '^- `assets/img/2016/09/2016-09-14-new-york\.jpg`' docs/alt-text-draft.md
grep -c '^- `assets/img/2016/05/2016-05-04-berlin\.jpg`' docs/alt-text-draft.md
grep -c '^- `assets/img/2025/05/2025-05-15-san-francisco\.jpg`' docs/alt-text-draft.md
grep -c '^- `assets/img/2021/06/2021-06-28-greater-london\.jpg`' docs/alt-text-draft.md
grep -c '^- `assets/img/2022/04/2022-04-07-greater-london\.jpg`' docs/alt-text-draft.md
```

Expected: each command outputs `1`. If any output `0`, stop and ask the user — the draft has drifted from the spec.

## Task 2: Rewrite Each Entry Atomically

**Files:**
- Modify: `docs/alt-text-draft.md`

For each entry in document order, repeat steps 1–5 below before moving to the next entry. Do not batch.

- [ ] **Step 1: Read the current entry text**

Note the path and the existing caption verbatim. Hold the exact line in mind for the `Edit` call later.

- [ ] **Step 2: Decide whether viewing is required**

Apply the heuristic from the design doc. Trigger viewing only if any of the four conditions is true:

- identifiable-person check (generic descriptor + suspicion of named person)
- location/context-leak check (place name not in filename and not obviously in image)
- interpretive-language verification (emotion / activity worth deciding on deliberately)
- substrate-vs-artwork ambiguity (cannot tell from text alone which is visually integral)

If none apply, skip step 3.

- [ ] **Step 3: View the image (only when step 2 triggered viewing)**

Call `view_image` on the absolute path, e.g.:

```text
/Users/jonathan/small-observations/assets/img/2024/01/2024-01-13-liverpool.jpg
```

Look only for the specific thing the trigger flagged — do not re-describe the whole image.

- [ ] **Step 4: Write the rewritten caption and replace the line in the file**

Apply criteria 1–9 from the design doc. Compose a single new caption.

Use the `Edit` tool with:
- `old_string` = the entire current line (including the leading `` - `` and trailing newline-free content)
- `new_string` = the same path-and-colon prefix followed by the new caption

Example shape of an `Edit` call:

- `old_string`: `` - `assets/img/2024/01/2024-01-13-liverpool.jpg`: Large building mural with a black-and-white portrait surrounded by colourful Beatles-inspired scenes. ``
- `new_string`: `` - `assets/img/2024/01/2024-01-13-liverpool.jpg`: <rewritten caption here>. ``

The path string between the backticks and the colon-space immediately after MUST be identical in `old_string` and `new_string`.

- [ ] **Step 5: Verify the path appears exactly once after the edit**

Run:

```bash
grep -c "^- \`<the exact path just edited>\`" docs/alt-text-draft.md
```

Expected: `1`. If `0`, the edit failed; re-investigate. If `2` or more, a duplicate has been introduced; stop.

- [ ] **Step 6: Repeat steps 1–5 for every remaining entry**

Continue in document order until the last line of the file is rewritten.

## Task 3: Verify The Finished Draft

**Files:**
- Read: `docs/alt-text-draft.md`

- [ ] **Step 1: Confirm line count is unchanged**

Run:

```bash
rg -c '^- `' docs/alt-text-draft.md
```

Expected: the same number as before Task 2 began (compare against `git show HEAD:docs/alt-text-draft.md | rg -c '^- `'`).

- [ ] **Step 2: Confirm path set is unchanged**

Run:

```bash
diff -u <(git show HEAD:docs/alt-text-draft.md | sed -n 's/^- `\([^`]*\)`.*/\1/p') <(sed -n 's/^- `\([^`]*\)`.*/\1/p' docs/alt-text-draft.md)
```

Expected: no diff output and exit code `0`. (Only captions should have changed; paths and ordering must match.)

- [ ] **Step 3: Check for duplicate paths**

Run:

```bash
sed -n 's/^- `\([^`]*\)`.*/\1/p' docs/alt-text-draft.md | sort | uniq -d
```

Expected: no output.

- [ ] **Step 4: Check for US spellings that slipped through**

Run:

```bash
rg -wn 'color|colors|gray|favorite|favorites|center|centers|organize|organized|organizing|organization|neighbor|neighbors' docs/alt-text-draft.md
```

Expected: no matches. If any appear, fix them with `Edit` calls and re-run.

- [ ] **Step 5: Spot-check the pre-identified viewing candidates**

For each pre-identified candidate from Task 1 Step 3, read the rewritten line and confirm:

- the criterion that flagged it (named person / location / interpretive language / substrate lead) has been addressed
- the path is unchanged
- the caption reads as a sentence on its own

## Task 4: Commit

**Files:**
- Commit: `docs/alt-text-draft.md`
- Leave untouched: any unrelated modified `content/posts/*.md` files (they remain unstaged)

- [ ] **Step 1: Review the scoped diff**

Run:

```bash
git status --short
git diff -- docs/alt-text-draft.md | head -80
```

Expected: `docs/alt-text-draft.md` is modified. Unrelated post edits may still be present but not staged.

- [ ] **Step 2: Stage only the corrected draft**

Run:

```bash
git add docs/alt-text-draft.md
git diff --cached --name-only
```

Expected output:

```text
docs/alt-text-draft.md
```

- [ ] **Step 3: Commit**

Run:

```bash
git commit -m "docs(photo): editorial pass on draft alt text"
```

Expected: commit succeeds, hook passes, only `docs/alt-text-draft.md` included.
