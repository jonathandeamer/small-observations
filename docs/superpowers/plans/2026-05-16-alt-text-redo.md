# Alt Text Redo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `docs/alt-text-draft.md` with correctly paired draft alt text for every image under `assets/img`.

**Architecture:** Treat each image path as an atomic unit. For each sorted path, view the exact image, draft one caption, append one line for that same path, and verify the last written line before continuing.

**Tech Stack:** Markdown, local filesystem, `view_image`, `apply_patch`, `find`, `sed`, `diff`, `rg`, `git`.

---

### Task 1: Reset The Draft File

**Files:**
- Modify: `docs/alt-text-draft.md`

- [ ] **Step 1: Replace the file with a header**

Use `apply_patch` to replace the current incorrect contents with:

```markdown
# Draft Alt Text For Image Assets

Draft alt text for the image files in `assets/img`, based on one-image-at-a-time visual review. Filename/path context such as date and location may inform wording, but the visible image is the primary source.
```

- [ ] **Step 2: Verify the file has no image entries yet**

Run: `rg -c '^- `' docs/alt-text-draft.md || true`

Expected: `0` or no count output.

### Task 2: Process Images Atomically

**Files:**
- Modify: `docs/alt-text-draft.md`

- [ ] **Step 1: Get the sorted source list**

Run:

```bash
find assets/img -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.gif' \) | sort
```

Expected: sorted image paths under `assets/img`.

- [ ] **Step 2: For each path, view one image**

Call `view_image` on the absolute path for exactly one image, for example:

```text
/Users/jonathan/small-observations/assets/img/2023/03/2023-03-20-new-york.jpg
```

- [ ] **Step 3: Append one caption for that exact path**

Use `apply_patch` to append one markdown line immediately after viewing the image:

```markdown
- `assets/img/2023/03/2023-03-20-new-york.jpg`: Large wall mural of a plastic bottle with fish inside and the words "Stop trashing our ocean now."
```

Do not hold multiple unwritten captions in memory. Do not append captions for paths that have not just been viewed.

- [ ] **Step 4: Verify the last line matches the just-viewed path**

Run:

```bash
tail -n 1 docs/alt-text-draft.md
```

Expected: the line begins with the exact same relative path just viewed.

- [ ] **Step 5: Repeat for every source image**

Continue steps 2-4 until every sorted image path has one entry.

### Task 3: Verify The Finished Draft

**Files:**
- Read: `docs/alt-text-draft.md`

- [ ] **Step 1: Compare entry count to image count**

Run:

```bash
find assets/img -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.gif' \) | wc -l
rg -c '^- `' docs/alt-text-draft.md
```

Expected: both commands report the same count.

- [ ] **Step 2: Compare filesystem paths to documented paths**

Run:

```bash
diff -u <(find assets/img -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.gif' \) | sort) <(sed -n 's/^- `\([^`]*\)`.*/\1/p' docs/alt-text-draft.md)
```

Expected: no diff output and exit code `0`.

- [ ] **Step 3: Check duplicate paths**

Run:

```bash
sed -n 's/^- `\([^`]*\)`.*/\1/p' docs/alt-text-draft.md | sort | uniq -d
```

Expected: no output.

- [ ] **Step 4: Spot-check previously wrong pairs**

Confirm in `docs/alt-text-draft.md`:

```markdown
- `assets/img/2023/03/2023-03-20-new-york.jpg`: Large wall mural of a plastic bottle with fish inside and the words "Stop trashing our ocean now."
```

Confirm `assets/img/2024/02/2024-02-25-barcelona-2.jpg` does not use the red bicycle caption.

### Task 4: Commit Corrected Draft

**Files:**
- Commit: `docs/alt-text-draft.md`
- Leave untouched: unrelated modified `content/posts/...` files

- [ ] **Step 1: Review the scoped diff**

Run:

```bash
git diff -- docs/alt-text-draft.md
git status --short
```

Expected: `docs/alt-text-draft.md` is modified; unrelated post changes may still be present but are not staged.

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
git commit -m "docs(photo): redo draft image alt text"
```

Expected: commit succeeds with only `docs/alt-text-draft.md` included.
