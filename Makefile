# Small Observations — common tasks
#
# `make` with no target prints help. The point of this file is to make the
# right thing the easy thing — especially: never run plain `hugo` (which adds
# to public/ without removing orphans). Always go through these targets.

.DEFAULT_GOAL := help
.PHONY: help dev build clean ingest ingest-dry test venv

help:  ## list available targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

dev:  ## hugo dev server (memfs, doesn't touch public/)
	hugo server --port 1313 --bind 127.0.0.1 --buildDrafts --buildFuture

build:  ## production build with orphan cleanup
	hugo --cleanDestinationDir --minify --gc

clean:  ## remove all generated output
	rm -rf public resources/_gen .hugo_build.lock

ingest:  ## ingest photos from _ingest/ (moves originals on success)
	. .venv/bin/activate && python -m ingest

ingest-dry:  ## ingest dry-run (doesn't move originals)
	. .venv/bin/activate && python -m ingest --dry-run

test:  ## run ingest tests
	. .venv/bin/activate && pytest

venv:  ## (re)create the python venv with dev deps
	python3 -m venv .venv
	. .venv/bin/activate && pip install -q -e ".[dev]"
