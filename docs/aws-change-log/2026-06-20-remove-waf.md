# 2026-06-20 — Remove WAF from CloudFront distribution

**Who:** jonathandeamer (via Claude Code)
**Account:** 017635961881
**Reason:** A CloudFront WAF web ACL (`CreatedByCloudFront-f770309f`) was attached
only to the `smallobservations.net` distribution, costing ~$8/mo ($5/web ACL +
$3 for 3 managed rule groups). The site is a static Hugo blog served from S3 via
CloudFront — no application server, DB, or forms — so the WAF (IP Reputation,
Common Rule Set, Known Bad Inputs) protects no real attack surface. It was never
referenced in this repo; appears to have been a console toggle flipped on ad-hoc
(first appeared in the bill in June 2026). Decision: remove it.

## Resources involved
- CloudFront distribution: `E25Q9EQNA4D7K1` (aliases: `smallobservations.net`,
  `www.smallobservations.net`)
- WAFv2 web ACL (CLOUDFRONT scope, us-east-1):
  - Name: `CreatedByCloudFront-f770309f`
  - Id: `fffaa35e-c5d5-430d-8dea-51d15ad86409`
  - ARN: `arn:aws:wafv2:us-east-1:017635961881:global/webacl/CreatedByCloudFront-f770309f/fffaa35e-c5d5-430d-8dea-51d15ad86409`
  - Rules: AWS-AWSManagedRulesAmazonIpReputationList, AWS-AWSManagedRulesCommonRuleSet, AWS-AWSManagedRulesKnownBadInputsRuleSet (default action: Allow)

## Backups (for revert)
- `2026-06-20-remove-waf-backup/distribution-config-before.json` — full distribution
  config + ETag (`E3AEGXETSR30VB`) before the change. `WebACLId` was the ARN above.
- `2026-06-20-remove-waf-backup/webacl-before.json` — full web ACL definition.

## Actions taken
1. **Detached WAF from distribution** — `cloudfront update-distribution` on
   `E25Q9EQNA4D7K1` with `WebACLId` set to `""` (IfMatch ETag `E3AEGXETSR30VB`).
   Result: accepted, status `InProgress` (redeploying).
2. **Deleted the web ACL** — `wafv2 delete-web-acl` after the distribution finished
   deploying. *(see status note at bottom)*

## How to revert
1. Recreate the web ACL from `webacl-before.json` (or re-toggle "security
   protections" in the CloudFront console — it recreates the same managed rule set).
2. Re-attach: set the distribution's `WebACLId` back to the ARN above via
   `cloudfront update-distribution` (or restore from `distribution-config-before.json`,
   updating the IfMatch ETag to the then-current one).

## Status log
- Step 1 (detach): DONE — distribution redeployed to `Deployed`, `WebACLId` = `""`.
- Step 2 (delete ACL): DONE — `wafv2 delete-web-acl` succeeded after deploy
  completed. `list-web-acls --scope CLOUDFRONT` now returns `[]`.
- Verification: `https://smallobservations.net/` returns HTTP 200; distribution
  status `Deployed` with no WAF.
- Expected billing impact: removes ~$8/mo WAF charge going forward. June will show
  a partial WAF charge for the days it was active.
