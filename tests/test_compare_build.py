from pathlib import Path

from scripts.compare_build import compare_trees, format_report, normalise_html


def page(head: str = "", body: str = "") -> str:
    return f"<!doctype html><html lang=en-gb><head>{head}</head><body>{body}</body></html>"


def write(root: Path, rel: str, content: str | bytes) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content)


def test_normalise_ignores_inline_css() -> None:
    a = page(head="<style>body{color:red}</style>")
    b = page(head="<style>body{color:blue;font-family:serif}</style>")
    assert normalise_html(a) == normalise_html(b)


def test_normalise_ignores_design_classes_attribute_order_and_whitespace() -> None:
    a = page(body='<div class="gallery-card old-name" id=x>  Hello\n  world </div>')
    b = page(body="<div id=x class=new-card>Hello world</div>")
    assert normalise_html(a) == normalise_html(b)


def test_normalise_keeps_microformat_classes() -> None:
    a = page(body='<article class="post h-entry">x</article>')
    b = page(body='<article class="post">x</article>')
    assert normalise_html(a) != normalise_html(b)


def test_normalise_keeps_contract_classes() -> None:
    a = page(body='<a class=skip-nav href="#main-content">Skip</a>')
    b = page(body='<a class=jump href="#main-content">Skip</a>')
    assert normalise_html(a) != normalise_html(b)


def test_normalise_keeps_text_links_and_style_attributes() -> None:
    base = page(body='<a href=/tags/ style="display: none;">tags</a>')
    assert normalise_html(base) != normalise_html(page(body='<a href=/tag/ style="display: none;">tags</a>'))
    assert normalise_html(base) != normalise_html(page(body='<a href=/tags/ style="display: none;">Tags</a>'))
    assert normalise_html(base) != normalise_html(page(body="<a href=/tags/>tags</a>"))


def test_normalise_keeps_head_metadata_and_jsonld() -> None:
    a = page(head='<link rel=canonical href=https://smallobservations.net/><script type=application/ld+json>{"a":1}</script>')
    b = page(head='<link rel=canonical href=https://smallobservations.net/><script type=application/ld+json>{"a":2}</script>')
    assert normalise_html(a) != normalise_html(b)


def test_identical_trees_pass(tmp_path: Path) -> None:
    for side in ("base", "head"):
        write(tmp_path / side, "index.html", page(body="<h1>Hi</h1>"))
        write(tmp_path / side, "feed.xml", "<rss/>")
    diff = compare_trees(tmp_path / "base", tmp_path / "head")
    assert not diff.failed


def test_css_and_design_class_only_change_passes(tmp_path: Path) -> None:
    write(tmp_path / "base", "index.html", page(head="<style>a{}</style>", body="<p class=tagline>x"))
    write(tmp_path / "head", "index.html", page(head="<style>b{}</style>", body="<p class=strapline>x"))
    assert not compare_trees(tmp_path / "base", tmp_path / "head").failed


def test_added_and_removed_files_fail(tmp_path: Path) -> None:
    write(tmp_path / "base", "img/a_hu_1.webp", b"a")
    write(tmp_path / "head", "img/a_hu_2.webp", b"a")
    diff = compare_trees(tmp_path / "base", tmp_path / "head")
    assert diff.failed
    assert diff.added == ["img/a_hu_2.webp"]
    assert diff.removed == ["img/a_hu_1.webp"]


def test_non_html_byte_change_fails(tmp_path: Path) -> None:
    write(tmp_path / "base", "feed.xml", "<rss>a</rss>")
    write(tmp_path / "head", "feed.xml", "<rss>b</rss>")
    diff = compare_trees(tmp_path / "base", tmp_path / "head")
    assert diff.changed == ["feed.xml"]
    assert diff.failed


def test_design_paths_are_reported_not_failed(tmp_path: Path) -> None:
    write(tmp_path / "base", "fonts/fraunces-latin.woff2", b"old")
    write(tmp_path / "head", "fonts/newfont.woff2", b"new")
    write(tmp_path / "base", "favicon.svg", "<svg>a</svg>")
    write(tmp_path / "head", "favicon.svg", "<svg>b</svg>")
    diff = compare_trees(tmp_path / "base", tmp_path / "head")
    assert not diff.failed
    assert diff.design_changes == ["favicon.svg", "fonts/fraunces-latin.woff2", "fonts/newfont.woff2"]


def test_html_change_fails_with_readable_diff(tmp_path: Path) -> None:
    write(tmp_path / "base", "404.html", page(body="<h1>Page not found.</h1>"))
    write(tmp_path / "head", "404.html", page(body="<h2>Page not found.</h2>"))
    diff = compare_trees(tmp_path / "base", tmp_path / "head")
    assert diff.changed == ["404.html"]
    assert "-<h1>" in diff.html_diffs["404.html"]
    assert "+<h2>" in diff.html_diffs["404.html"]
    report = format_report(diff)
    assert "404.html" in report
    assert "+<h2>" in report
