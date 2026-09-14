from pathlib import Path

from scripts.check_microformats import audit_post, audit_posts

POST = (
    "<!doctype html><html><head><title>t</title></head><body><main>"
    "<article class=\"post h-entry\">"
    "<h1 class=\"post-title p-name\">Brown bird</h1>"
    "<picture><img class=\"u-photo u-featured\" src=/img/a.jpg alt=a></picture>"
    "<p class=post-meta><time class=\"tnum dt-published\" datetime=2025-12-01T10:00:00Z>1 December 2025</time>"
    "<a rel=author class=\"p-author h-card\" href=https://jonathandeamer.com style=\"display: none;\">Jonathan Deamer</a>"
    "</article></main></body></html>"
)


def test_accepts_complete_h_entry() -> None:
    assert audit_post(POST, "p.html") == []


def test_requires_single_h_entry() -> None:
    assert audit_post(POST.replace("post h-entry", "post"), "p.html") == ["p.html: expected 1 h-entry, found 0"]


def test_requires_non_empty_name() -> None:
    assert audit_post(POST.replace(">Brown bird<", "><"), "p.html") == ["p.html: missing non-empty p-name"]


def test_name_may_be_visually_hidden() -> None:
    assert audit_post(POST.replace("post-title p-name", "post-title sr-only p-name"), "p.html") == []


def test_requires_photo_with_src() -> None:
    assert audit_post(POST.replace("u-photo u-featured", "photo"), "p.html") == ["p.html: missing <img class=u-photo src=...>"]


def test_requires_published_datetime() -> None:
    assert audit_post(POST.replace(" datetime=2025-12-01T10:00:00Z", ""), "p.html") == [
        "p.html: missing dt-published with datetime attribute"
    ]


def test_requires_author_card_with_href() -> None:
    assert audit_post(POST.replace("p-author h-card", "author"), "p.html") == [
        "p.html: missing p-author h-card with href"
    ]


def test_properties_must_follow_h_entry_start() -> None:
    moved = POST.replace("<article class=\"post h-entry\">", "").replace("</article>", "<div class=h-entry></div>")
    assert audit_post(moved, "p.html") == [
        "p.html: missing non-empty p-name",
        "p.html: missing <img class=u-photo src=...>",
        "p.html: missing dt-published with datetime attribute",
        "p.html: missing p-author h-card with href",
    ]


def test_audit_posts_skips_alias_redirects(tmp_path: Path) -> None:
    good = tmp_path / "2025/12/brown-bird/index.html"
    good.parent.mkdir(parents=True)
    good.write_text(POST)
    alias = tmp_path / "2025/12/old/index.html"
    alias.parent.mkdir(parents=True)
    alias.write_text("<html><head><meta http-equiv=refresh content=\"0; url=/x/\"></head></html>")
    assert audit_posts(tmp_path) == []
