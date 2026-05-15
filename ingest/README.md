# Ingest

Turn original smartphone photos into Hugo posts.

## Setup (once)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

1. Drop original JPEGs into `_ingest/` (any folder structure within is fine).
2. Activate the venv: `source .venv/bin/activate`
3. Run: `python -m ingest`
4. Each photo with date + GPS EXIF produces:
   - `content/posts/YYYY-MM-DD-<city>.md` — front matter prefilled; `title:`, `tags:`, `artists:` blank for you to fill in
   - `assets/img/YYYY/MM/YYYY-MM-DD-<city>.jpg` — web-sized (1600px long edge, q82)
5. Successfully processed originals move to `_ingest/_processed/`. Photos missing GPS or EXIF date are logged to `_ingest/_missing-location.log` and the original stays put.

Use `--dry-run` to process without moving originals.

## Notes

- Reverse geocoding uses OpenStreetMap Nominatim. First lookup for a given coordinate hits the network; subsequent lookups within ~10m hit the cache at `.cache/geocode.json`.
- City names come from Nominatim's `city` → `town` → `village` → `hamlet` → `suburb` → `municipality` fallback chain. If none of those exist, the photo is skipped.
- EXIF `DateTimeOriginal` is treated as UTC. Apple iPhones store the local-time offset in a separate `OffsetTimeOriginal` field that this script does not currently read; if precise local time matters for a post, edit the `date:` field in the generated markdown by hand.
- After ingest, manually fill in `tags:`, `artists:`, optional `title:`, and commentary in the body of each generated markdown file before publishing.

## Tests

```bash
pytest
```

Test fixtures are auto-generated in `tests/fixtures/` at the start of each session (gitignored).
