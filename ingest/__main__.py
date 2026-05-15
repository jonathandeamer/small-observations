"""Command-line entry: process every photo under _ingest/.

Usage:
    python -m ingest [--ingest DIR] [--dry-run]

Behavior:
- Scans `_ingest/` (default) for .jpg/.jpeg files (recursively).
- Skips files inside `_ingest/_processed/`.
- For each photo, runs the pipeline.
- On success: moves the original to `_ingest/_processed/`.
- On skip: appends a line to `_ingest/_missing-location.log`.
- Prints a summary at the end.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from ingest import pipeline


def _gather_existing_slugs(content_root: Path) -> set[str]:
    if not content_root.exists():
        return set()
    return {p.stem for p in content_root.glob("*.md") if p.stem != "_index"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ingest")
    parser.add_argument("--ingest", type=Path, default=Path("_ingest"),
                        help="Directory containing original photos (default: _ingest)")
    parser.add_argument("--content", type=Path, default=Path("content/posts"),
                        help="Hugo content output dir (default: content/posts)")
    parser.add_argument("--assets", type=Path, default=Path("assets/img"),
                        help="Hugo asset output dir (default: assets/img)")
    parser.add_argument("--cache", type=Path, default=Path(".cache/geocode.json"),
                        help="Geocode cache file (default: .cache/geocode.json)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Process but do not move originals to _processed/")
    args = parser.parse_args(argv)

    ingest_dir: Path = args.ingest
    processed_dir = ingest_dir / "_processed"
    log_path = ingest_dir / "_missing-location.log"

    if not ingest_dir.exists():
        print(f"error: {ingest_dir} does not exist", file=sys.stderr)
        return 2

    sources = [
        p for p in ingest_dir.rglob("*")
        if p.is_file()
        and p.suffix.lower() in {".jpg", ".jpeg"}
        and processed_dir not in p.parents
    ]
    if not sources:
        print(f"no .jpg/.jpeg files found under {ingest_dir}")
        return 0

    existing_slugs = _gather_existing_slugs(args.content)
    publish_date = datetime.now(timezone.utc).replace(microsecond=0)

    ok = skip = err = 0
    for src in sorted(sources):
        result = pipeline.process(
            source=src,
            content_root=args.content,
            asset_root=args.assets,
            existing_slugs=existing_slugs,
            publish_date=publish_date,
            cache_path=args.cache,
        )
        if result.status == "ok":
            ok += 1
            existing_slugs.add(result.slug)
            if not args.dry_run:
                processed_dir.mkdir(parents=True, exist_ok=True)
                src.rename(processed_dir / src.name)
            print(f"  ok    {src.name} -> {result.slug}")
        elif result.status == "skip":
            skip += 1
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a") as f:
                f.write(f"{datetime.now().isoformat()}\t{src}\t{result.reason}\n")
            print(f"  skip  {src.name} ({result.reason})")
        else:
            err += 1
            print(f"  ERROR {src.name}: {result.reason}", file=sys.stderr)

    print(f"\ndone: {ok} processed, {skip} skipped, {err} errors")
    return 0 if err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
