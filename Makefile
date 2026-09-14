# Small Observations — common tasks
#
# `make` with no target prints help. The point of this file is to make the
# right thing the easy thing — especially: never run plain `hugo` (which adds
# to public/ without removing orphans). Always go through these targets.

.DEFAULT_GOAL := help
.PHONY: help dev build check audit clean deploy deploy-dry ingest ingest-dry test venv stats

# First real post page (alias redirect pages contain http-equiv and are skipped).
# Recursive (=) so it's evaluated after build has produced public/.
SAMPLE_POST = $(firstword $(shell grep -L 'http-equiv' public/[0-9]*/*/*/index.html 2>/dev/null))

# One page per template family. Extend when a new template is added.
PA11Y_PAGES = public/index.html $(SAMPLE_POST) public/posts/index.html \
	public/posts/page/2/index.html public/tags/index.html public/tags/by-count/index.html \
	public/tags/favourite/index.html public/cities/index.html public/countries/index.html \
	public/artists/index.html public/years/index.html public/years/2018/index.html \
	public/404.html

help:  ## list available targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

dev:  ## hugo dev server (memfs, doesn't touch public/)
	hugo server --port 1313 --bind 127.0.0.1 --buildDrafts --buildFuture

build:  ## production build with orphan cleanup
	hugo --cleanDestinationDir --minify --gc --printPathWarnings

check: build  ## build then run every audit; fails on the first failing audit
	@$(MAKE) --no-print-directory audit

audit:  ## run every audit against the existing public/ (no rebuild)
	@test -f public/index.html || { echo "public/ is empty — run make build first"; exit 1; }
	@echo "→ photo post front matter:"
	@python3 scripts/check_post_frontmatter.py content/posts
	@echo
	@echo "→ photo post slugs:"
	@python3 scripts/audit_slugs.py
	@echo "    ok"
	@echo
	@echo "→ posts with empty alt text on their photo:"
	@python3 scripts/check_photo_alt.py public
	@echo
	@echo "→ rendered post metadata:"
	@python3 scripts/check_rendered_metadata.py public
	@echo
	@echo "→ RSS, sitemap, and llms.txt URL contracts:"
	@python3 scripts/check_feed_sitemap.py public content/posts
	@echo
	@if command -v htmltest >/dev/null 2>&1; then \
		set -e; \
		echo "→ htmltest (internal link check):"; \
		htmltest -s public; \
	else \
		echo "→ htmltest not installed (skipping link check)"; \
		echo "    install with: brew install htmltest"; \
	fi
	@echo
	@if command -v pa11y >/dev/null 2>&1; then \
		set -e; \
		for page in $(PA11Y_PAGES); do \
			echo "→ pa11y $$page"; \
			pa11y --config pa11y.json "file://$(CURDIR)/$$page"; \
		done; \
	else \
		echo "→ pa11y not installed (skipping accessibility check)"; \
		echo "    install with: npm install -g pa11y"; \
	fi
	@echo
	@if java -jar ~/.vnu/vnu.jar --version >/dev/null 2>&1; then \
		set -e; \
		echo "→ vnu HTML validation (homepage + one post):"; \
		java -jar ~/.vnu/vnu.jar --skip-non-html public/index.html $(SAMPLE_POST); \
		echo "    ok"; \
	else \
		echo "→ vnu HTML validator not installed (skipping)"; \
		echo "    install: mkdir -p ~/.vnu && curl -sL https://github.com/validator/validator/releases/latest/download/vnu.jar -o ~/.vnu/vnu.jar"; \
	fi
	@echo
	@echo "→ sitemap:"
	@test -s public/sitemap.xml && xmllint --noout public/sitemap.xml
	@echo "    ok ($$(grep -o '<loc>' public/sitemap.xml | wc -l | tr -d ' ') URLs)"
	@echo
	@echo "→ RSS feed validity:"
	@xmllint --noout public/feed.xml
	@echo "    ok"
	@echo

clean:  ## remove all generated output
	rm -rf public resources/_gen .hugo_build.lock

deploy: build  ## deploy production build to S3 and invalidate CloudFront
	AWS_PROFILE=hugo-deploy hugo deploy --target production

deploy-dry: build  ## show production deploy changes without uploading
	AWS_PROFILE=hugo-deploy hugo deploy --target production --dryRun

ingest:  ## ingest photos from _ingest/ (moves originals on success)
	. .venv/bin/activate && python -m ingest

ingest-dry:  ## ingest dry-run (reports slugs; writes and moves nothing)
	. .venv/bin/activate && python -m ingest --dry-run

test:  ## run ingest tests
	. .venv/bin/activate && pytest

venv:  ## (re)create the python venv with dev deps
	python3 -m venv .venv
	. .venv/bin/activate && pip install -q -e ".[dev]"

stats:  ## generate weekly traffic report from CloudFront logs
	python3 scripts/generate_traffic_report.py
