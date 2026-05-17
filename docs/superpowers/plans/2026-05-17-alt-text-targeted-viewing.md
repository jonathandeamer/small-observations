# Alt Text Targeted Viewing Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** View every image in `docs/alt-text-draft.md` not on the skip list from `docs/superpowers/specs/2026-05-17-alt-text-targeted-viewing-design.md`, and update each entry's caption when viewing surfaces an identifiable person, additional embedded text, an artist signature, a substrate correction, or a more specific style descriptor. Leave entries unchanged when viewing surfaces nothing new.

**Architecture:** Batched view-then-edit. Read 10–15 images per round in parallel (via the `Read` tool, which handles JPEGs as images), note any change needed per image, then apply edits one entry at a time using exact-string `Edit` calls. Path-to-caption pairing is preserved structurally because only the caption text after the colon is rewritten.

**Tech Stack:** Markdown, local filesystem, `Read` (for image viewing), `Edit` (for in-place caption replacement), `rg`, `sed`, `diff`, `git`.

---

## Task 1: Build The Work List

**Files:**
- Read: `docs/superpowers/specs/2026-05-17-alt-text-targeted-viewing-design.md`
- Read: `docs/alt-text-draft.md`

- [ ] **Step 1: Read the design doc end-to-end**

The five lookup priorities and the skip list must be loaded into context for the entire pass. Re-reading mid-pass is fine.

- [ ] **Step 2: Build the in-scope path list**

Run:

```bash
{
  sed -n 's/^- `\([^`]*\)`.*/\1/p' docs/alt-text-draft.md
} > /tmp/all-paths.txt

cat > /tmp/skip-paths.txt <<'EOF'
assets/img/2016/05/2016-05-04-berlin.jpg
assets/img/2016/09/2016-09-14-new-york.jpg
assets/img/2017/08/2017-08-04-greater-london.jpg
assets/img/2021/06/2021-06-28-greater-london.jpg
assets/img/2022/04/2022-04-07-greater-london.jpg
assets/img/2023/05/2023-05-05-liverpool.jpg
assets/img/2024/01/2024-01-13-liverpool.jpg
assets/img/2024/02/2024-02-25-barcelona.jpg
assets/img/2025/05/2025-05-15-san-francisco.jpg
assets/img/2015/10/2015-10-12-greater-london.jpg
assets/img/2016/11/2016-11-19-greater-london.jpg
assets/img/2022/03/2022-03-15-greater-london.jpg
assets/img/2022/09/2022-09-24-derbyshire-dales.jpg
assets/img/2024/03/2024-03-16-leeds.jpg
assets/img/2025/07/2025-07-25-reykjavikurborg.jpg
assets/img/2025/07/2025-07-26-reykjavikurborg-2.jpg
assets/img/2025/11/2025-11-03-chicago.jpg
assets/img/2025/12/2025-12-04-greater-london.jpg
assets/img/2026/02/2026-02-17-greater-london.jpg
EOF

grep -vxFf /tmp/skip-paths.txt /tmp/all-paths.txt > /tmp/view-paths.txt
wc -l /tmp/view-paths.txt
```

Expected: line count is roughly 90 (109 total minus 19 skipped).

- [ ] **Step 3: Pre-record the baseline line count for verification later**

Run:

```bash
git show HEAD:docs/alt-text-draft.md | grep -c '^- `' > /tmp/baseline-count.txt
cat /tmp/baseline-count.txt
```

Expected: `109`.

## Task 2: Batch-View And Edit

**Files:**
- Modify: `docs/alt-text-draft.md`

Process `/tmp/view-paths.txt` in document order, 10–15 images per batch. Repeat steps 1–4 for each batch until the list is exhausted.

- [ ] **Step 1: Pick the next batch of 10–15 paths from the work list**

Take the next contiguous block of unprocessed paths. Track which paths have been processed (e.g., by appending to `/tmp/done-paths.txt`).

- [ ] **Step 2: View all images in the batch in parallel**

Issue one `Read` tool call per path in the batch, all in a single message to the model. Use absolute paths, e.g. `/Users/jonathan/small-observations/<path-from-list>`.

- [ ] **Step 3: For each viewed image, decide change vs no change**

For each image, work through the five lookup items in the design doc:

1. Identifiable people, characters, figures?
2. Embedded text the current caption summarises or omits?
3. Artist signature visible?
4. Substrate misnamed?
5. More specific style descriptor warranted?

If none apply, the entry is unchanged — move on.

If any apply, draft the updated caption following all editorial criteria from the previous pass (artwork leads, British English, no "image of", quoted text verbatim).

- [ ] **Step 4: Apply edits with exact-string `Edit` calls**

For each entry that needs a change, call `Edit` with:
- `old_string` = the entire current line, exactly as it appears in `docs/alt-text-draft.md`
- `new_string` = same path-and-colon prefix, then the updated caption

The path string between the backticks and the colon-space immediately after MUST be identical in `old_string` and `new_string`.

Example shape (illustrative — the actual entries will vary):

- `old_string`: `` - `assets/img/2025/04/2025-04-27-liverpool.jpg`: A footballer in a red kit, painted in red-and-white stained-glass-style panels on a black brick wall. ``
- `new_string`: `` - `assets/img/2025/04/2025-04-27-liverpool.jpg`: A stained-glass-style portrait of <named footballer> in a red kit, painted on a black brick wall. ``

- [ ] **Step 5: Append processed paths to the done list**

Run for the batch just finished:

```bash
cat >> /tmp/done-paths.txt <<'EOF'
<paste batch paths, one per line>
EOF
```

This is bookkeeping in case of interruption.

- [ ] **Step 6: Continue with the next batch**

Repeat steps 1–5 until `/tmp/done-paths.txt` contains every path in `/tmp/view-paths.txt`. Verify with:

```bash
sort /tmp/view-paths.txt > /tmp/view-paths.sorted
sort /tmp/done-paths.txt > /tmp/done-paths.sorted
diff -u /tmp/view-paths.sorted /tmp/done-paths.sorted
```

Expected: no diff and exit code `0`.

## Task 3: Verify The Finished Draft

**Files:**
- Read: `docs/alt-text-draft.md`

- [ ] **Step 1: Confirm line count is unchanged**

Run:

```bash
new=$(grep -c '^- `' docs/alt-text-draft.md)
old=$(cat /tmp/baseline-count.txt)
echo "old=$old new=$new"
[ "$old" = "$new" ] && echo "OK" || echo "MISMATCH"
```

Expected: `OK`.

- [ ] **Step 2: Confirm path set is unchanged**

Run:

```bash
diff -u <(git show HEAD:docs/alt-text-draft.md | sed -n 's/^- `\([^`]*\)`.*/\1/p') <(sed -n 's/^- `\([^`]*\)`.*/\1/p' docs/alt-text-draft.md)
```

Expected: no diff output and exit code `0`.

- [ ] **Step 3: Check for duplicate paths**

Run:

```bash
sed -n 's/^- `\([^`]*\)`.*/\1/p' docs/alt-text-draft.md | sort | uniq -d
```

Expected: no output.

- [ ] **Step 4: Check for US spellings that slipped through**

Run:

```bash
rg -wn -E 'color|colors|gray|favorite|favorites|center|centers|organize|organized|organizing|organization|neighbor|neighbors|colorful|stylized|stenciled|ladybug' docs/alt-text-draft.md
```

Expected: no matches.

- [ ] **Step 5: Spot-check changed entries**

Run:

```bash
git diff -- docs/alt-text-draft.md | grep -E '^\+- `' | head -30
```

Read the listed updates. Each should clearly improve on the previous version by adding a named person, a quoted phrase, a signature, or a substrate correction — not by mere paraphrase.

## Task 4: Commit

**Files:**
- Commit: `docs/alt-text-draft.md`
- Leave untouched: unrelated modified `content/posts/*.md` files

- [ ] **Step 1: Review the scoped diff**

Run:

```bash
git status --short
git diff -- docs/alt-text-draft.md | head -80
```

Expected: only `docs/alt-text-draft.md` is modified for staging; unrelated post edits remain unstaged.

- [ ] **Step 2: Stage only the corrected draft**

Run:

```bash
git add docs/alt-text-draft.md
git diff --cached --name-only
```

Expected:

```text
docs/alt-text-draft.md
```

- [ ] **Step 3: Commit**

Run:

```bash
git commit -m "docs(photo): targeted viewing pass on draft alt text"
```

Expected: commit succeeds, hook passes, only `docs/alt-text-draft.md` included.
