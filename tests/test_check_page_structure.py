from pathlib import Path

from scripts.check_page_structure import audit_page, audit_site

HEAD = (
    "<title>t</title>"
    "<link rel=alternate type=application/rss+xml href=https://smallobservations.net/feed.xml>"
    "<link rel=icon type=image/svg+xml href=/favicon.svg>"
    "<link rel=icon type=image/x-icon href=/favicon.ico>"
    "<link rel=apple-touch-icon href=/apple-touch-icon.png>"
    "<link rel=preload href=/fonts/f.woff2 as=font type=font/woff2 crossorigin>"
    "<link rel=canonical href=https://smallobservations.net/x/>"
)
NAV = (
    '<nav class=masthead-browse aria-label="Browse the archive">'
    "<a href=/posts/>latest</a><a href=/tags/>tags</a><a href=/cities/>cities</a>"
    "<a href=/years/>years</a><a href=/countries/>countries</a><a href=/artists/>artists</a>"
    "</nav>"
)


def html(head: str = HEAD, body: str = "") -> str:
    return f"<!doctype html><html lang=en-gb><head>{head}</head><body>{body}</body></html>"


def home_body(img: str = "<img src=/a.jpg alt=a loading=eager fetchpriority=high>") -> str:
    return (
        "<a class=skip-nav href=#main-content>Skip to content</a>"
        "<main class=page id=main-content><header class=masthead>"
        "<a href=/><h1 class=masthead-title>Small<span>·</span>Observations</h1></a>"
        f"{NAV}</header><h2>A few favourites</h2>{img}<img src=/b.jpg alt=b loading=lazy></main>"
    )


def inner_body(main: str = "<h1>Tags</h1>") -> str:
    return (
        "<a class=skip-nav href=#main-content>Skip to content</a>"
        "<main class=page id=main-content><header class=masthead>"
        "<a href=/><p class=masthead-title>Small<span>·</span>Observations</p></a>"
        f"{NAV}</header>{main}</main>"
    )


def public(tmp_path: Path) -> Path:
    (tmp_path / "fonts").mkdir(exist_ok=True)
    (tmp_path / "fonts/f.woff2").write_bytes(b"x")
    return tmp_path


def test_accepts_valid_home_and_inner_pages(tmp_path: Path) -> None:
    pub = public(tmp_path)
    assert audit_page(html(body=home_body()), "index.html", pub, is_home=True) == []
    assert audit_page(html(body=inner_body()), "tags/index.html", pub, is_home=False) == []


def test_requires_exactly_one_h1(tmp_path: Path) -> None:
    pub = public(tmp_path)
    assert audit_page(html(body=inner_body("<h2>Tags</h2>")), "p.html", pub, False) == ["p.html: expected 1 <h1>, found 0"]
    assert audit_page(html(body=inner_body("<h1>A</h1><h1>B</h1>")), "p.html", pub, False) == [
        "p.html: expected 1 <h1>, found 2"
    ]


def test_site_title_is_h1_only_on_home(tmp_path: Path) -> None:
    pub = public(tmp_path)
    body = inner_body("").replace("<p class=masthead-title>", "<h1 class=masthead-title>").replace(
        "Observations</p>", "Observations</h1>"
    )
    assert audit_page(html(body=body), "p.html", pub, False) == [
        "p.html: site title must be <p class=masthead-title> on non-home pages",
        "p.html: <h1> must describe the page, not be the site title",
    ]
    home = home_body().replace("<h1 class=masthead-title>", "<h1>")
    assert audit_page(html(body=home), "index.html", pub, True) == [
        "index.html: home <h1> must be the site title (class masthead-title)"
    ]


def test_skip_link_must_be_first_and_target_main(tmp_path: Path) -> None:
    pub = public(tmp_path)
    body = "<div></div>" + inner_body()
    assert audit_page(html(body=body), "p.html", pub, False) == [
        "p.html: first element in <body> must be <a class=skip-nav href=#main-content>"
    ]
    body = inner_body().replace("<main class=page id=main-content>", "<div id=main-content>").replace("</main>", "</div>")
    assert audit_page(html(body=body), "p.html", pub, False) == ["p.html: #main-content must be a <main> element"]


def test_browse_nav_needs_all_six_links_and_label(tmp_path: Path) -> None:
    pub = public(tmp_path)
    body = inner_body().replace("<a href=/artists/>artists</a>", "").replace(' aria-label="Browse the archive"', "")
    assert audit_page(html(body=body), "p.html", pub, False) == [
        "p.html: <nav class=masthead-browse> needs an aria-label",
        "p.html: browse nav missing links to /artists/",
    ]


def test_head_links_required(tmp_path: Path) -> None:
    pub = public(tmp_path)
    head = HEAD.replace("<link rel=apple-touch-icon href=/apple-touch-icon.png>", "").replace(
        "https://smallobservations.net/feed.xml", "/index.xml"
    )
    assert audit_page(html(head=head, body=inner_body()), "p.html", pub, False) == [
        "p.html: RSS autodiscovery must point at https://smallobservations.net/feed.xml",
        "p.html: missing head link /apple-touch-icon.png",
    ]


def test_preload_targets_must_exist(tmp_path: Path) -> None:
    pub = public(tmp_path)
    head = HEAD.replace("/fonts/f.woff2", "/fonts/renamed.woff2")
    assert audit_page(html(head=head, body=inner_body()), "p.html", pub, False) == [
        "p.html: preload /fonts/renamed.woff2 does not exist in public/"
    ]


def test_home_first_image_wins_lcp(tmp_path: Path) -> None:
    pub = public(tmp_path)
    body = home_body(img="<img src=/a.jpg alt=a loading=lazy>")
    assert audit_page(html(body=body), "index.html", pub, True) == [
        "index.html: first <img> must have loading=eager and fetchpriority=high"
    ]


def test_audit_site_skips_alias_redirects_and_detects_home(tmp_path: Path) -> None:
    pub = public(tmp_path)
    (pub / "index.html").write_text(html(body=home_body()))
    alias = pub / "2022/11/old/index.html"
    alias.parent.mkdir(parents=True)
    alias.write_text(
        "<!doctype html><html><head><title>x</title>"
        "<meta http-equiv=refresh content=\"0; url=https://smallobservations.net/new/\"></head></html>"
    )
    assert audit_site(pub) == []
