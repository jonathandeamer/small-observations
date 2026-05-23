from pathlib import Path

from scripts.check_post_frontmatter import audit_posts


def write_post(path: Path, frontmatter: str) -> None:
    path.parent.mkdir(parents=True)
    path.write_text(f"---\n{frontmatter.strip()}\n---\n")


VALID_FRONTMATTER = """
slug: "london-brown-bird"
date: 2025-12-04T08:24:43Z
publishDate: 2026-05-15T14:53:33Z
photo: 2025/12/london-brown-bird.jpg
title: "Brown bird on a branch amid abstract graffiti, London"
description: "Brown bird on a branch. 2025."
alt: "A brown bird on a branch surrounded by bright abstract graffiti shapes."
countries: [United Kingdom]
cities: [London]
artists: []
tags: [birds, animals]
years: [2025]
weight: 0
exif:
  camera: "iPhone"
"""


def test_accepts_complete_photo_post_frontmatter(tmp_path: Path) -> None:
    write_post(tmp_path / "content/posts/complete.md", VALID_FRONTMATTER)

    assert audit_posts(tmp_path / "content/posts") == []


def test_reports_missing_required_keys_and_empty_editorial_fields(tmp_path: Path) -> None:
    write_post(
        tmp_path / "content/posts/broken.md",
        """
slug: ""
date: 2025-12-04T08:24:43Z
publishDate: 2026-05-15T14:53:33Z
photo: 2025/12/london-brown-bird.jpg
title: ""
description: "   "
alt: ""
countries: [United Kingdom]
cities: [London]
artists: []
tags: []
weight: 0
""",
    )

    assert audit_posts(tmp_path / "content/posts") == [
        "broken.md: missing required key 'years'",
        "broken.md: missing required key 'exif'",
        "broken.md: 'slug' must be non-empty",
        "broken.md: 'title' must be non-empty",
        "broken.md: 'description' must be non-empty",
        "broken.md: 'alt' must be non-empty",
    ]


def test_reports_list_shape_and_year_mismatch(tmp_path: Path) -> None:
    write_post(
        tmp_path / "content/posts/broken.md",
        VALID_FRONTMATTER.replace("tags: [birds, animals]", 'tags: "birds"').replace("years: [2025]", "years: [2024]"),
    )

    assert audit_posts(tmp_path / "content/posts") == [
        "broken.md: 'tags' must be an inline list",
        "broken.md: 'years' must include date year 2025",
    ]


def test_reports_invalid_alias_paths(tmp_path: Path) -> None:
    write_post(
        tmp_path / "content/posts/broken.md",
        VALID_FRONTMATTER + """
aliases: ["/2025/12/old-slug", "2025/12/relative-slug/", "https://smallobservations.net/2025/12/full-url/"]
""",
    )

    assert audit_posts(tmp_path / "content/posts") == [
        "broken.md: aliases must be absolute site paths with trailing slash: /2025/12/old-slug",
        "broken.md: aliases must be absolute site paths with trailing slash: 2025/12/relative-slug/",
        "broken.md: aliases must be absolute site paths, not full URLs: https://smallobservations.net/2025/12/full-url/",
    ]
