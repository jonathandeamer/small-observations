# 2026-06-20 — AWS cost review session

**Who:** jonathandeamer (via Claude Code)
**Account:** 017635961881 (IAM user `jonathandeamer`)
**Goal:** Review AWS spend and cut waste. Three changes made (all reversible),
plus a list of outstanding opportunities.

> Note: this account hosts more than just this site (other domains, personal
> backups, a podcast archive). It's logged here because this is the only repo
> with an AWS change-log; the changes themselves are mostly account-wide, not
> specific to Small Observations. The one site-specific change (WAF removal) has
> its own file: [`2026-06-20-remove-waf.md`](./2026-06-20-remove-waf.md).

---

## 1. Cost baseline (Cost Explorer, UnblendedCost incl. tax)

| Month | Total |
|---|---|
| Dec 2025 | $35.88 |
| Jan 2026 | $36.66 |
| Feb 2026 | $76.41 ⬆ |
| Mar 2026 | $40.44 |
| Apr 2026 | $43.59 |
| May 2026 | $76.84 ⬆ |
| Jun 2026 (partial) | $50.77 |

Baseline ~$40/mo. The two ~$76 spikes (Feb, May) = annual **domain renewals**
(Amazon Registrar $15–17) landing on top of higher **Lightsail** months.

**Main cost drivers:** S3 (~$28–31/mo, almost all of it one Arq backup), Lightsail
(spiky), Registrar (lumpy renewals), Route 53 hosted zones (~$1.5–2), KMS (~$1),
GuardDuty (~$0.10), Tax (UK VAT 20%).

---

## 2. Changes made (all done, all reversible)

### 2a. Removed CloudFront WAF — saves ~$8/mo
Full detail in [`2026-06-20-remove-waf.md`](./2026-06-20-remove-waf.md). Summary:
deleted the auto-created `CreatedByCloudFront-f770309f` web ACL that was attached
only to the `smallobservations.net` distribution. A static S3+CloudFront blog has
no attack surface for the managed rule sets to protect. Detached from distribution
`E25Q9EQNA4D7K1`, waited for redeploy, deleted the ACL. Backups + revert steps in
that file.

### 2b. `nbn-episodes` S3 bucket → Glacier Instant Retrieval — saves ~$1.8/mo
- Private bucket (no public access, no website config), 1703 objects / ~104 GB of
  podcast `.mp3` files + a `Books/` PDF archive. All was in S3 Standard (~$2.2/mo).
- Cold archive, plain files (no backup-tool index), so a direct storage-class
  change is safe.
- **Action:** one-shot in-place server-side copy:
  ```
  aws s3 cp s3://nbn-episodes/ s3://nbn-episodes/ --recursive \
    --storage-class GLACIER_IR --metadata-directive COPY --only-show-errors
  ```
- **Result:** 1688 objects → GLACIER_IR; 15 zero-byte folder-marker keys (`.../`)
  left in Standard (intentional — avoids Glacier IR's 128 KB-minimum billing).
  Bucket is unversioned, so no old-version bloat.
- Storage now ~$0.4/mo. Still millisecond access. New terms: 90-day min storage +
  $0.03/GB retrieval (negligible for a cold archive).
- **Revert:** same copy with `--storage-class STANDARD`.

### 2c. `miranda-macbook-backup` S3 bucket → Glacier IR via lifecycle — saves ~$23/mo
- This bucket is an **Arq 7 backup** of a MacBook (layout: `backupconfig.json`,
  `backupfolders`, `backuprecords`). 136,617 objects, **~1.2 TB, 100% S3 Standard**,
  no lifecycle, versioning suspended. Active (newest writes 2026-06-19).
- It was ~$28/mo — almost the entire S3 bill and ~half the whole AWS baseline. The
  other two Arq buckets (`jd-photos-arq-backup`, `jd-red-seagate-1tb-backup`) were
  already in Deep Archive; this one was just left on Standard.

**Why not fix it in Arq:** Arq 7 (v7.28.1) sets the S3 storage class at
storage-location *creation* and does not let you edit it afterward. Confirmed the
other two buckets have **no** storage-class lifecycle rules — Arq wrote them
directly as Deep Archive. Changing it in Arq would mean deleting + re-creating the
location and re-uploading 1.2 TB. Not worth it.

**Why Glacier IR (not Deep Archive):** Glacier IR objects are *directly readable*
with no restore step (verified: HEAD shows `GLACIER_IR`, `Restore: null`, and a
direct ranged GET returned data). So Arq keeps working unchanged. Deep Archive
would make Arq's metadata non-instant and break browsing without a ~12h restore.
Deep Archive would save ~$3/mo more but isn't worth the re-upload + loss of instant
access.

**Cost-safety check (the one real risk):** Glacier IR charges $0.03/GB on reads, so
if Arq's periodic *validation* re-read the 1.2 TB it could cost more than Standard.
Checked Cost Explorer egress for eu-west-1 backups: **~0.0002–0.002 GB/month**
(would be ~1200 GB if validating). Validation is not running → clean win.

- **Action:** lifecycle rule `arq-packs-to-glacier-ir` on the bucket:
  - Filter: `ObjectSizeGreaterThan: 131072` (keeps Arq's small metadata in Standard)
  - Transition: → `GLACIER_IR`, 30 days after creation (delay avoids 90-day-min
    penalties on short-lived churn; existing 1.2 TB is all older, so it transitions
    in the next ~24–48h evaluation)
- **Status when written:** rule applied + verified via
  `get-bucket-lifecycle-configuration`. Actual object transitions happen
  asynchronously over ~24–48h — NOT yet confirmed flipped at time of writing.
  (S3 also auto-added `TransitionDefaultMinimumObjectSize: all_storage_classes_128K`
  as a backstop.)
- **Expected:** ~$28/mo → ~$5–6/mo on this bucket.
- **Revert:**
  ```
  aws s3api delete-bucket-lifecycle --bucket miranda-macbook-backup
  aws s3 cp s3://miranda-macbook-backup/ s3://miranda-macbook-backup/ \
    --recursive --storage-class STANDARD --metadata-directive COPY
  ```

---

## 3. S3 bucket inventory (sizes/classes at time of review)

| Bucket | Region | Size | Class | ~$/mo | Note |
|---|---|---|---|---|---|
| miranda-macbook-backup | eu-west-1 | 1245 GiB | Standard → **Glacier IR** (rule) | $28→~$5 | Arq backup |
| nbn-episodes | eu-west-2 | 96.7 GiB | **Glacier IR** (done) | $2.2→~$0.4 | podcast archive |
| jd-photos-arq-backup | eu-west-1 | 55 GiB | Deep Archive | ~$0.06 | already optimal |
| jd-red-seagate-1tb-backup | eu-west-1 | 12 GiB | Deep Archive | ~$0.01 | already optimal |
| book-dragon | eu-west-2 | 0.21 GiB | Standard | ~$0 | negligible |
| smallobservations.net | eu-west-2 | 0.24 GiB | Standard | ~$0 | the blog — leave |
| jonathandeamer.com | eu-west-2 | 6 obj / 0.7 MB | Standard | ~$0 | near-empty; verify not a live CF origin before touching |
| jd-macbook-arq-backup-2025 | eu-west-2 | 0 objects | — | $0 | **empty** — safe to delete |
| jd-tilde-team-backup | eu-central-1 | ~1 MB | — | ~$0 | near-empty (CloudWatch reads denied in that region) |

---

## 4. Savings tally

| Action | Status | Saving/mo |
|---|---|---|
| Removed CloudFront WAF | done | ~$8 |
| nbn-episodes → Glacier IR | done | ~$1.8 |
| miranda Arq backup → Glacier IR (lifecycle) | done (transition completes ~24–48h) | ~$23 |
| **Total** | | **~$33/mo (~$395/yr)** |

Brings the ~$40/mo baseline toward ~$7–8/mo steady state (plus lumpy domain renewals).

---

## 5. Outstanding / not yet done

- **Verify the miranda transition** ~24–48h after 2026-06-20: re-check storage-class
  distribution and realised Glacier IR size.
- **Lightsail** — spiky ($1–17/mo): identify what's spun up/down and any orphaned
  snapshots / static IPs / stopped-but-billing instances. Not investigated yet.
- **Amazon Registrar / domains** — list domains, confirm which to keep on
  auto-renew (these drive the Feb/May bill spikes).
- **Cleanup:** delete empty `jd-macbook-arq-backup-2025`; decide on near-empty
  `jd-tilde-team-backup` and `jonathandeamer.com` (check the latter isn't the live
  origin for the `.com` CloudFront distribution first).
- **Optional deeper cut:** miranda → Deep Archive (~$3/mo more) would require
  re-creating the Arq storage location and re-uploading 1.2 TB — decided not worth it.
- **Optional hygiene:** add `AbortIncompleteMultipartUpload` cleanup to the Arq
  backup buckets (orphaned multipart parts bill silently).
