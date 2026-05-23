from pathlib import Path

from scripts.check_rendered_metadata import audit_rendered_posts


def write_page(path: Path, head: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"<!doctype html><html><head>{head}</head><body></body></html>")


VALID_HEAD = """
<title>Brown bird · Small Observations</title>
<link rel="canonical" href="https://smallobservations.net/2025/12/london-brown-bird/">
<link rel="alternate" type="application/rss+xml" title="Small Observations" href="https://smallobservations.net/feed.xml">
<meta property="og:title" content="Brown bird · Small Observations">
<meta property="og:description" content="Brown bird on a branch. 2025.">
<meta property="og:image" content="https://smallobservations.net/img/bird.jpg">
<meta name="twitter:card" content="summary_large_image">
"""


def test_accepts_post_with_required_rendered_metadata(tmp_path: Path) -> None:
    write_page(tmp_path / "public/2025/12/london-brown-bird/index.html", VALID_HEAD)

    assert audit_rendered_posts(tmp_path / "public") == []


def test_ignores_hugo_alias_redirect_pages(tmp_path: Path) -> None:
    write_page(
        tmp_path / "public/2025/12/old-slug/index.html",
        """
<title>https://smallobservations.net/2025/12/london-brown-bird/</title>
<link rel="canonical" href="https://smallobservations.net/2025/12/london-brown-bird/">
<meta http-equiv="refresh" content="0; url=https://smallobservations.net/2025/12/london-brown-bird/">
""",
    )
    write_page(tmp_path / "public/2025/12/london-brown-bird/index.html", VALID_HEAD)

    assert audit_rendered_posts(tmp_path / "public") == []


def test_ignores_banksy_brush_alias_redirect_to_mallet_slug(tmp_path: Path) -> None:
    write_page(
        tmp_path / "public/2025/08/new-york-banksy-child-brush/index.html",
        """
<title>https://smallobservations.net/2025/08/new-york-banksy-child-mallet/</title>
<link rel="canonical" href="https://smallobservations.net/2025/08/new-york-banksy-child-mallet/">
<meta http-equiv="refresh" content="0; url=https://smallobservations.net/2025/08/new-york-banksy-child-mallet/">
""",
    )
    write_page(
        tmp_path / "public/2025/08/new-york-banksy-child-mallet/index.html",
        VALID_HEAD.replace("Brown bird", "Banksy child swinging a mallet")
        .replace("london-brown-bird", "new-york-banksy-child-mallet")
        .replace("Brown bird on a branch", "Black silhouette painted beside red fire-sprinkler signs"),
    )

    assert audit_rendered_posts(tmp_path / "public") == []


def test_reports_missing_and_empty_rendered_metadata(tmp_path: Path) -> None:
    write_page(
        tmp_path / "public/2025/12/london-brown-bird/index.html",
        """
<title>   </title>
<link rel="canonical" href="">
<meta property="og:title" content="">
<meta property="og:image" content="https://smallobservations.net/img/bird.jpg">
""",
    )

    assert audit_rendered_posts(tmp_path / "public") == [
        "2025/12/london-brown-bird/index.html: missing non-empty <title>",
        "2025/12/london-brown-bird/index.html: missing non-empty canonical link",
        "2025/12/london-brown-bird/index.html: missing RSS autodiscovery link",
        "2025/12/london-brown-bird/index.html: missing non-empty og:title",
        "2025/12/london-brown-bird/index.html: missing non-empty og:description",
        "2025/12/london-brown-bird/index.html: missing non-empty twitter:card",
    ]
