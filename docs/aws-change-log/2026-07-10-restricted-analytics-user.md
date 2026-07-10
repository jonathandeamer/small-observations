# 2026-07-10 — Create restricted IAM user for local GoAccess analytics

## Goal

Create a single-purpose, restricted programmatic IAM user (`smallobservations-analytics`) to retrieve CloudFront access logs for local GoAccess analysis. This avoids the need to run interactive, browser-based SSO authentication (`aws login`) which expires periodically.

## AWS resources

- **IAM User:** `smallobservations-analytics`
- **IAM Policy:** `SmallObservationsAnalyticsRead` (ARN: `arn:aws:iam::017635961881:policy/SmallObservationsAnalyticsRead`)
- **Log bucket:** `smallobservations-cloudfront-logs`
- **Restricted Log Prefix:** `cloudfront/E25Q9EQNA4D7K1/*`

## IAM Policy Configuration

The policy restricts the user to list the log bucket and retrieve log objects under the specific CloudFront distribution prefix, adhering to the Principle of Least Privilege:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowListLogBucket",
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::smallobservations-cloudfront-logs"
        },
        {
            "Sid": "AllowReadLogObjects",
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::smallobservations-cloudfront-logs/cloudfront/E25Q9EQNA4D7K1/*"
        }
    ]
}
```

## Local Configuration

The user's programmatic access keys are stored in `~/.aws/credentials` under the `[smallobservations-analytics]` profile, and its region default `eu-west-2` is configured in `~/.aws/config`.

This enables non-interactive log syncing:
```sh
AWS_PROFILE=smallobservations-analytics aws s3 sync \
  s3://smallobservations-cloudfront-logs/cloudfront/E25Q9EQNA4D7K1/ \
  tmp/goaccess/logs/
```

## Verification

Testing the newly generated access key `AKIAQIGZPNQM72MONGVO` via the sync dryrun successfully lists and retrieves bucket content:

```sh
AWS_PROFILE=smallobservations-analytics aws s3 sync \
  s3://smallobservations-cloudfront-logs/cloudfront/E25Q9EQNA4D7K1/ \
  tmp/goaccess/logs/ \
  --dryrun
```

Output:
```text
(dryrun) download: s3://smallobservations-cloudfront-logs/cloudfront/E25Q9EQNA4D7K1/E25Q9EQNA4D7K1.2026-07-10-13.3905a8ac.gz to tmp/goaccess/logs/E25Q9EQNA4D7K1.2026-07-10-13.3905a8ac.gz
...
```

## Rollback

To completely remove the IAM policy, user, and access keys:

```sh
# 1. Delete the access key
aws iam delete-access-key \
  --user-name smallobservations-analytics \
  --access-key-id AKIAQIGZPNQM72MONGVO

# 2. Detach the policy from the user
aws iam detach-user-policy \
  --user-name smallobservations-analytics \
  --policy-arn arn:aws:iam::017635961881:policy/SmallObservationsAnalyticsRead

# 3. Delete the IAM user
aws iam delete-user \
  --user-name smallobservations-analytics

# 4. Delete the IAM policy
aws iam delete-policy \
  --policy-arn arn:aws:iam::017635961881:policy/SmallObservationsAnalyticsRead
```

Also remove the `[smallobservations-analytics]` and `[profile smallobservations-analytics]` blocks from `~/.aws/credentials` and `~/.aws/config`.
