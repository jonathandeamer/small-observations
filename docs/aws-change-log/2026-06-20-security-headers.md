# 2026-06-20 — Add security response headers to CloudFront

**What:** Created a CloudFront response-headers policy and attached it to the
`smallobservations.net` distribution's default cache behaviour, so every response
carries HSTS, CSP, and the standard hardening headers. Zero added AWS cost —
response-headers policies are free and add no per-request charge.

## Resources

- CloudFront distribution: `E25Q9EQNA4D7K1` (aliases: `smallobservations.net`)
- Response-headers policy: `small-observations-security-headers`
  - ID: `8bf658c2-7896-4b78-be46-e93460368078`
- AWS account: `017635961881`, run with the `default` profile (`jonathandeamer`
  user). The `hugo-deploy` profile is S3-sync + invalidation only and **cannot**
  read or modify distribution config or response-headers policies — use `default`
  for any CloudFront config change.

## Headers applied

- `Strict-Transport-Security: max-age=63072000; includeSubDomains`
  (preload **not** set — see note below)
- `Content-Security-Policy: default-src 'self'; img-src 'self'; style-src 'self'
  'unsafe-inline'; font-src 'self'; script-src 'none'; object-src 'none';
  base-uri 'self'; form-action 'none'; frame-ancestors 'none';
  upgrade-insecure-requests`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: accelerometer=(), autoplay=(), camera=(), display-capture=(),
  encrypted-media=(), fullscreen=(), geolocation=(), gyroscope=(), magnetometer=(),
  microphone=(), midi=(), payment=(), picture-in-picture=(), usb=(),
  xr-spatial-tracking=()`

### Why the CSP is this tight

The site has **no JavaScript, no third-party requests, no inline `style=`
attributes, no external images/iframes**. The only `<style>` is Hugo's inlined,
fingerprinted CSS block (hence `style-src 'unsafe-inline'`); fonts and images are
self-hosted (`'self'`). `script-src 'none'` is safe because there is no JS to run.
If JS, an external resource, or an embed is ever added, this CSP must be widened
or the affected resource will be blocked.

## Notes / reversal

- **HSTS preload is intentionally off.** Enabling `preload` (and submitting to
  hstspreload.org) is a hard-to-undo, browser-baked commitment that all subdomains
  serve HTTPS forever. Easy to enable later if wanted — flip `Preload` to true in
  the policy and submit the domain.
- **Reversal:** detach by setting the default cache behaviour's
  `ResponseHeadersPolicyId` back to empty via `cloudfront update-distribution`
  (restore from `2026-06-20-security-headers-backup/distribution-config-before.json`,
  which has no RHP attached), then optionally
  `cloudfront delete-response-headers-policy --id 8bf658c2-7896-4b78-be46-e93460368078`.

## Backup files

- `2026-06-20-security-headers-backup/distribution-config-before.json` — full
  distribution config + ETag before the change (no RHP attached).
- `2026-06-20-security-headers-backup/policy-created.json` — create-policy response.
- `2026-06-20-security-headers-backup/update-result.json` — update-distribution response.

## Status

- DONE. Policy created and attached; distribution redeployed to `Deployed`.
- Verified live (`curl -sI https://smallobservations.net/`): all six headers
  present (HSTS, CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy,
  Permissions-Policy). Homepage returns HTTP 200; a sample gallery image
  (`/img/2025/11/2025-11-03-chicago_hu_*.jpg`) returns HTTP 200 `image/jpeg`,
  confirming the CSP blocks nothing on the live site.
