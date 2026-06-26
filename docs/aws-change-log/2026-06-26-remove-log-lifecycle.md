# 2026-06-26 — Remove 30-day expiry on CloudFront log bucket

## Goal

Stop deleting CloudFront access logs after 30 days so they accumulate
indefinitely, enabling all-time GoAccess analytics (top referrers, landing
pages, traffic over months) rather than a rolling 30-day window.

This reverses the retention decision in
[`2026-06-21-goaccess-logging.md`](2026-06-21-goaccess-logging.md), which added
the `expire-cloudfront-logs-after-30-days` lifecycle rule. Logging itself,
bucket security, and the local GoAccess workflow are unchanged.

## AWS resources

- Log bucket: `smallobservations-cloudfront-logs` (`eu-west-2`)
- Log prefix: `cloudfront/E25Q9EQNA4D7K1/`
- Lifecycle rule being removed: `expire-cloudfront-logs-after-30-days`

## State before the change

```json
{
    "TransitionDefaultMinimumObjectSize": "all_storage_classes_128K",
    "Rules": [
        {
            "Expiration": { "Days": 30 },
            "ID": "expire-cloudfront-logs-after-30-days",
            "Filter": { "Prefix": "" },
            "Status": "Enabled"
        }
    ]
}
```

Captured to
`docs/aws-change-log/2026-06-26-remove-log-lifecycle-backup/lifecycle-before.json`.

## Cost analysis (why this is safe)

Measured log volume at current traffic (4 full days, 22–25 Jun 2026):

- **~285 KB/day compressed → ~8.4 MB/month.**

S3 Standard in `eu-west-2` is `$0.024/GB-month`. Storage is cumulative, so the
charge grows on the accumulating pile:

| After     | Total stored | That month's S3 storage cost |
|-----------|--------------|------------------------------|
| 6 months  | ~50 MB       | ~$0.001                      |
| 12 months | ~100 MB      | ~$0.0024                     |
| 3 years   | ~300 MB      | ~$0.007                      |
| 5 years   | ~500 MB      | ~$0.012                      |

A full year of all-time data costs **~1–2 cents total**; five years stays under
a dollar. Log-delivery PUT requests (~7,500/month at `$0.0053/1,000` ≈
`$0.04/month`) are unchanged — they happen regardless of retention.

Storage class was deliberately left as Standard: at this object size, the
minimum-object-size and transition-request fees of Glacier/Infrequent Access
would cost more than just keeping everything in Standard.

The only real cost is non-monetary: CloudFront writes ~250 tiny files/day
(~91k/year), so over time `aws s3 sync` and the GoAccess parse get slower and
the local `tmp/goaccess/logs/` tree grows large in file count. Revisit with a
monthly roll-up/aggregation step if that becomes annoying.

## Change to make

Delete the lifecycle configuration entirely (the bucket has only this one rule):

```sh
aws s3api delete-bucket-lifecycle \
  --bucket smallobservations-cloudfront-logs
```

## Verification

```sh
aws s3api get-bucket-lifecycle-configuration \
  --bucket smallobservations-cloudfront-logs
```

Expected after the change:

```text
An error occurred (NoSuchLifecycleConfiguration) ... The lifecycle
configuration does not exist
```

That error is the success signal — no rules means nothing expires. Existing
logs already older than 30 days are gone (they were expired under the old rule);
accumulation starts fresh from the current set forward.

## Rollback

Restore the original 30-day expiry rule:

```sh
aws s3api put-bucket-lifecycle-configuration \
  --bucket smallobservations-cloudfront-logs \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "expire-cloudfront-logs-after-30-days",
        "Filter": { "Prefix": "" },
        "Status": "Enabled",
        "Expiration": { "Days": 30 }
      }
    ]
  }'
```

(Equivalent to `2026-06-26-remove-log-lifecycle-backup/lifecycle-before.json`;
the `TransitionDefaultMinimumObjectSize` field in that capture is a read-time
default and does not need to be re-supplied.)

## Backup files

```text
docs/aws-change-log/2026-06-26-remove-log-lifecycle-backup/
  lifecycle-before.json   # lifecycle config as it was before removal
```
