# 2026-06-21 — Enable CloudFront logs for GoAccess analytics

## Goal

Enable no-JavaScript analytics for `smallobservations.net` by delivering
CloudFront standard access logs to S3, then analysing those logs locally with
GoAccess.

This avoids Google Analytics, site JavaScript, cookies, CloudWatch Logs,
Kinesis, Firehose, Athena, OpenSearch, and any always-on analytics service.

## AWS resources

- CloudFront distribution: `E25Q9EQNA4D7K1`
- Site aliases: `smallobservations.net`, `www.smallobservations.net`
- Origin: `smallobservations.net.s3-website.eu-west-2.amazonaws.com`
- Log bucket: `smallobservations-cloudfront-logs`
- Log prefix: `cloudfront/E25Q9EQNA4D7K1/`
- Cookies in logs: disabled

## Changes made

1. Created S3 bucket `smallobservations-cloudfront-logs` in `eu-west-2`.
2. Enabled S3 Block Public Access on the log bucket:
   - `BlockPublicAcls = true`
   - `IgnorePublicAcls = true`
   - `BlockPublicPolicy = true`
   - `RestrictPublicBuckets = true`
3. Set bucket ownership controls to `BucketOwnerPreferred`, which is required
   for CloudFront legacy standard logging because log delivery uses ACLs.
4. Added a lifecycle rule, `expire-cloudfront-logs-after-30-days`, expiring all
   log objects after 30 days.
5. Enabled CloudFront standard logging on `E25Q9EQNA4D7K1`:
   - bucket: `smallobservations-cloudfront-logs.s3.amazonaws.com`
   - prefix: `cloudfront/E25Q9EQNA4D7K1/`
   - include cookies: `false`

The CloudFront distribution deployed successfully after the update.

## Verification

Fresh checks after the change:

```sh
aws cloudfront get-distribution-config \
  --id E25Q9EQNA4D7K1 \
  --query 'DistributionConfig.Logging'
```

Returned:

```json
{
  "Enabled": true,
  "IncludeCookies": false,
  "Bucket": "smallobservations-cloudfront-logs.s3.amazonaws.com",
  "Prefix": "cloudfront/E25Q9EQNA4D7K1/"
}
```

Bucket checks confirmed:

- S3 Block Public Access is enabled.
- ownership controls are `BucketOwnerPreferred`.
- lifecycle expiry is 30 days.
- the bucket ACL includes the CloudFront log-delivery canonical user grant.

Two live requests were generated:

```text
https://smallobservations.net/         200
https://smallobservations.net/feed.xml 200
```

No log object had arrived immediately after enabling logging. That is expected:
CloudFront standard log delivery is delayed and best-effort.

## Cost notes

At setup time, recent CloudFront traffic was about 28,433 requests over 31 days
and 0.78 GiB delivered. CloudFront cost for the checked period was reported as
`$0` in Cost Explorer.

AWS Pricing API values checked on 2026-06-21 for S3 Standard in `eu-west-2`:

- storage: `$0.024/GB-month` for the first 50 TB
- GET and similar requests: `$0.0042/10,000`
- PUT/COPY/POST/LIST requests: `$0.0053/1,000`

Expected incremental cost for this log bucket with 30-day retention is well
under `$0.01/month` at current traffic. This is not guaranteed to stay true if
traffic or AWS pricing changes.

Avoid enabling CloudFront real-time logs, CloudWatch Logs delivery, Kinesis,
Firehose, Athena, or OpenSearch for this purpose unless the cost model is
reviewed again.

## Local GoAccess workflow

Install:

```sh
brew install goaccess
```

Download logs locally:

```sh
mkdir -p _analytics/cloudfront-logs
aws s3 sync \
  s3://smallobservations-cloudfront-logs/cloudfront/E25Q9EQNA4D7K1/ \
  _analytics/cloudfront-logs/
```

Generate a static HTML report:

```sh
find _analytics/cloudfront-logs -name '*.gz' -exec gzip -dc {} + |
  goaccess - \
    --log-format=CLOUDFRONT \
    --date-format=CLOUDFRONT \
    --time-format=CLOUDFRONT \
    --ignore-crawlers \
    -o _analytics/goaccess.html
```

`_analytics/` should remain local and uncommitted.

## Rollback

Disable CloudFront logging:

```sh
aws cloudfront get-distribution-config \
  --id E25Q9EQNA4D7K1 \
  > /tmp/smallobservations-cloudfront-config.json

jq '.DistributionConfig.Logging = {
      "Enabled": false,
      "IncludeCookies": false,
      "Bucket": "",
      "Prefix": ""
    } | .DistributionConfig' \
  /tmp/smallobservations-cloudfront-config.json \
  > /tmp/smallobservations-cloudfront-disable-logging.json

aws cloudfront update-distribution \
  --id E25Q9EQNA4D7K1 \
  --if-match "$(jq -r '.ETag' /tmp/smallobservations-cloudfront-config.json)" \
  --distribution-config file:///tmp/smallobservations-cloudfront-disable-logging.json
```

Then optionally remove the log bucket after any retained logs are no longer
needed:

```sh
aws s3 rm s3://smallobservations-cloudfront-logs/ --recursive
aws s3api delete-bucket --bucket smallobservations-cloudfront-logs
```

## Backup files

The pre-change CloudFront config and update response are stored in:

```text
docs/aws-change-log/2026-06-21-goaccess-logging-backup/
```
