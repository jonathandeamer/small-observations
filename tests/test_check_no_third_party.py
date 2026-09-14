from pathlib import Path

from scripts.check_no_third_party import (
    audit_html,
    deploy_matcher_errors,
    font_budget_errors,
)


def page(head: str = "", body: str = "") -> str:
    return f"<!doctype html><html><head>{head}</head><body>{body}</body></html>"


def test_accepts_local_resources_and_navigational_external_links() -> None:
    html = page(
        head=(
            "<style>@font-face{src:url(/fonts/f.woff2)}</style>"
            "<link rel=icon href=/favicon.svg>"
            "<link rel=preload href=/fonts/f.woff2 as=font>"
            "<link rel=canonical href=https://smallobservations.net/>"
            "<link rel=alternate type=application/rss+xml href=https://smallobservations.net/feed.xml>"
            "<link rel=me href=https://tilde.zone/@JonathanDeamer>"
            "<script type=application/ld+json>{}</script>"
        ),
        body=(
            '<img src=/img/a.jpg srcset="/img/a_200.webp 200w, /img/a_400.webp 400w">'
            "<a href=https://jonathandeamer.com>me</a>"
            '<span style="background:url(data:image/png;base64,AAAA)"></span>'
        ),
    )
    assert audit_html(html, "index.html") == []


def test_rejects_executable_script() -> None:
    assert audit_html(page(body="<script>alert(1)</script>"), "x.html") == [
        "x.html: <script> without type=application/ld+json"
    ]


def test_rejects_script_src_even_with_jsonld_type() -> None:
    errors = audit_html(page(body="<script type=application/ld+json src=/a.json></script>"), "x.html")
    assert errors == ["x.html: <script> with src=/a.json"]


def test_rejects_external_stylesheet_and_preconnect() -> None:
    html = page(
        head=(
            "<link rel=preconnect href=https://fonts.gstatic.com>"
            "<link rel=stylesheet href=https://fonts.googleapis.com/css2?family=Inter>"
        )
    )
    assert audit_html(html, "x.html") == [
        "x.html: <link rel=preconnect> loads off-site https://fonts.gstatic.com",
        "x.html: <link rel=stylesheet> loads off-site https://fonts.googleapis.com/css2?family=Inter",
    ]


def test_rejects_external_image_src_and_srcset() -> None:
    html = page(body='<img src=https://cdn.example.com/a.jpg srcset="/a.jpg 1x, https://cdn.example.com/b.jpg 2x">')
    assert audit_html(html, "x.html") == [
        "x.html: <img src> loads off-site https://cdn.example.com/a.jpg",
        "x.html: <img srcset> loads off-site https://cdn.example.com/b.jpg",
    ]


def test_rejects_embedding_elements() -> None:
    assert audit_html(page(body="<iframe src=/a.html></iframe>"), "x.html") == ["x.html: <iframe> not allowed"]


def test_rejects_css_import_and_external_url() -> None:
    html = page(head="<style>@import url(/a.css);body{background:url('https://example.com/bg.png')}</style>")
    assert audit_html(html, "x.html") == [
        "x.html: CSS @import not allowed",
        "x.html: CSS url() loads off-site https://example.com/bg.png",
    ]


def test_rejects_external_url_in_style_attribute() -> None:
    html = page(body='<div style="background:url(//example.com/a.png)"></div>')
    assert audit_html(html, "x.html") == ["x.html: CSS url() loads off-site //example.com/a.png"]


def test_css_budget() -> None:
    html = page(head="<style>" + "a{}" * 10 + "</style>")
    assert audit_html(html, "x.html", max_css_bytes=10) == [
        "x.html: inline CSS is 30 bytes (budget 10)"
    ]


def test_font_budget(tmp_path: Path) -> None:
    (tmp_path / "fonts").mkdir()
    (tmp_path / "fonts/a.woff2").write_bytes(b"x" * 8)
    (tmp_path / "fonts/b.woff2").write_bytes(b"x" * 8)
    assert font_budget_errors(tmp_path, max_font_bytes=16) == []
    assert font_budget_errors(tmp_path, max_font_bytes=15) == ["fonts/: 16 bytes (budget 15)"]


TOML = """
[[deployment.matchers]]
  pattern = "^.+\\\\.html$"
[[deployment.matchers]]
  pattern = "^.+\\\\.(?:woff2|woff)$"
"""


def test_every_file_needs_a_deploy_matcher(tmp_path: Path) -> None:
    for rel in ("index.html", "fonts/a.woff2", "fonts/a.otf", "favicon.ico", "robots.txt"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")
    assert deploy_matcher_errors(tmp_path, TOML) == [
        "fonts/a.otf: matches no [[deployment.matchers]] pattern (would deploy without Cache-Control)"
    ]


def test_deploy_matcher_skips_files_hugo_deploy_skips(tmp_path: Path) -> None:
    # hugo deploy skips .DS_Store and hidden directories, except .well-known.
    for rel in (".impeccable/hook.cache.json", "img/.DS_Store", ".well-known/security.txt"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")
    assert deploy_matcher_errors(tmp_path, TOML) == [
        ".well-known/security.txt: matches no [[deployment.matchers]] pattern (would deploy without Cache-Control)"
    ]
