# Small Observations — common tasks
#
# `make` with no target prints help. The point of this file is to make the
# right thing the easy thing — especially: never run plain `hugo` (which adds
# to public/ without removing orphans). Always go through these targets.

.DEFAULT_GOAL := help
.PHONY: help dev build check clean ingest ingest-dry test venv

help:  ## list available targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

dev:  ## hugo dev server (memfs, doesn't touch public/)
	hugo server --port 1313 --bind 127.0.0.1 --buildDrafts --buildFuture

build:  ## production build with orphan cleanup
	hugo --cleanDestinationDir --minify --gc --printPathWarnings

check: build  ## build then sanity-check the rendered site
	@echo
	@echo "→ posts with empty alt text on their photo:"
	@grep -rL 'alt="[^"]\+"' public/2*/*/*/index.html 2>/dev/null | head -20 \
		| sed 's|^|    |' || echo "    (none — all posts have alt text, or no post pages exist)"
	@echo
	@if command -v htmltest >/dev/null 2>&1; then \
		echo "→ htmltest (internal link check):"; \
		htmltest -s public 2>&1 | tail -15; \
	else \
		echo "→ htmltest not installed (skipping link check)"; \
		echo "    install with: brew install htmltest"; \
	fi
	@echo
	@if command -v pa11y >/dev/null 2>&1; then \
		echo "→ pa11y (accessibility audit on homepage):"; \
		pa11y "file://$(PWD)/public/index.html" 2>&1 | tail -20; \
	else \
		echo "→ pa11y not installed (skipping accessibility check)"; \
		echo "    install with: npm install -g pa11y"; \
	fi
	@echo

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
