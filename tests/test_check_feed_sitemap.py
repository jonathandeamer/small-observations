from pathlib import Path

from scripts.check_feed_sitemap import audit_feed_and_sitemap


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n")


def write_valid_llms_txt(public: Path) -> None:
    write(
        public / "llms.txt",
        """
# Small Observations

> A notebook of street art I've enjoyed and photographed since 2005, browsable by city, artist, year, and tag.

Small Observations is a static Hugo photo archive. Each post is one photographed artwork or street-art sighting. Post dates are the dates the photos were taken; the RSS feed is ordered by publish date. Alt text describes what is visible in each image.

This file is a navigation aid for agents and readers. It is not a licence grant and does not replace robots.txt.

## Core

- [Home](https://smallobservations.net/): Curated favourite photos and entry points into the archive.
- [Latest posts](https://smallobservations.net/posts/): All photo posts, ordered by photo date.
- [RSS feed](https://smallobservations.net/feed.xml): Newest published posts.
- [Sitemap](https://smallobservations.net/sitemap.xml): Complete indexable URL list.

## Browse the archive

- [Favourites](https://smallobservations.net/tags/favourite/): Selected photos the author keeps coming back to.
- [Tags](https://smallobservations.net/tags/): Subjects, themes, context, and styles.
- [Tags by count](https://smallobservations.net/tags/by-count/): Tags ordered by frequency.
- [Cities](https://smallobservations.net/cities/): Posts grouped by city.
- [Countries](https://smallobservations.net/countries/): Posts grouped by country.
- [Years](https://smallobservations.net/years/): Posts grouped by year photographed.
- [Artists](https://smallobservations.net/artists/): Posts grouped by identified artist.

## About the author

- [Jonathan Deamer](https://jonathandeamer.com/): Maintainer of this site. His personal homepage links to professional background, Wikipedia editing, software projects, social profiles, and contact details.
""",
    )


def test_accepts_feed_and_sitemap_contract(tmp_path: Path) -> None:
    public = tmp_path / "public"
    content = tmp_path / "content/posts"
    write_valid_llms_txt(public)
    write(
        content / "post.md",
        """
---
slug: "london-brown-bird"
date: 2025-12-04T08:24:43Z
publishDate: 2026-05-15T14:53:33Z
---
""",
    )
    write(
        public / "feed.xml",
        """
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <atom:link href="https://smallobservations.net/feed.xml" rel="self" type="application/rss+xml"/>
    <item>
      <link>https://smallobservations.net/2025/12/london-brown-bird/</link>
      <pubDate>Fri, 15 May 2026 14:53:33 +0000</pubDate>
      <content:encoded><![CDATA[
        <p><a href="https://smallobservations.net/2025/12/london-brown-bird/"><img src="https://smallobservations.net/images/bird.jpg" alt="A brown bird on a wall."></a></p>
      ]]></content:encoded>
    </item>
  </channel>
</rss>
""",
    )
    write(
        public / "sitemap.xml",
        """
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://smallobservations.net/2025/12/london-brown-bird/</loc>
    <lastmod>2026-05-15T14:53:33+00:00</lastmod>
  </url>
</urlset>
""",
    )

    assert audit_feed_and_sitemap(public, content) == []


def test_reports_feed_and_sitemap_regressions(tmp_path: Path) -> None:
    public = tmp_path / "public"
    content = tmp_path / "content/posts"
    write_valid_llms_txt(public)
    write(
        content / "post.md",
        """
---
slug: "london-brown-bird"
date: 2025-12-04T08:24:43Z
publishDate: 2026-05-15T14:53:33Z
---
""",
    )
    write(
        public / "feed.xml",
        """
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <atom:link href="https://smallobservations.net/" rel="self" type="application/rss+xml"/>
    <managingEditor>Jonathan</managingEditor>
    <webMaster>Jonathan</webMaster>
    <item>
      <link>https://smallobservations.net/2025/12/london-brown-bird/</link>
      <pubDate>Fri, 15 May 2026 14:53:33 +0000</pubDate>
      <content:encoded><![CDATA[
        <p><a href="https://smallobservations.net/2025/12/london-brown-bird/"><img src="https://smallobservations.net/images/bird.jpg" alt="A brown bird on a wall."></a></p>
      ]]></content:encoded>
    </item>
    <item><link>https://smallobservations.net/404/</link><pubDate>Fri, 15 May 2026 14:53:32 +0000</pubDate></item>
    <item><link>https://smallobservations.net/tags/by-count/</link><pubDate>Fri, 15 May 2026 14:53:31 +0000</pubDate></item>
  </channel>
</rss>
""",
    )
    write(
        public / "sitemap.xml",
        """
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://smallobservations.net/2025/12/london-brown-bird/</loc>
    <lastmod>2025-12-04T08:24:43+00:00</lastmod>
  </url>
  <url><loc>https://smallobservations.net/404/</loc></url>
</urlset>
""",
    )

    assert audit_feed_and_sitemap(public, content) == [
        "feed.xml: atom self link must be https://smallobservations.net/feed.xml",
        "feed.xml: managingEditor must be omitted or contain an email address",
        "feed.xml: webMaster must be omitted or contain an email address",
        "feed.xml: RSS item is not a photo post: https://smallobservations.net/404/",
        "feed.xml: RSS item is not a photo post: https://smallobservations.net/tags/by-count/",
        "sitemap.xml: must not include https://smallobservations.net/404/",
        "sitemap.xml: https://smallobservations.net/2025/12/london-brown-bird/ lastmod 2025-12-04T08:24:43+00:00 should use publishDate 2026-05-15T14:53:33+00:00",
    ]


def test_reports_non_apex_feed_and_sitemap_urls(tmp_path: Path) -> None:
    public = tmp_path / "public"
    content = tmp_path / "content/posts"
    write_valid_llms_txt(public)
    write(
        content / "post.md",
        """
---
slug: "london-brown-bird"
date: 2025-12-04T08:24:43Z
publishDate: 2026-05-15T14:53:33Z
---
""",
    )
    write(
        public / "feed.xml",
        """
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <atom:link href="https://foo.smallobservations.net/feed.xml" rel="self" type="application/rss+xml"/>
    <item>
      <link>https://www.smallobservations.net/2025/12/london-brown-bird/</link>
      <pubDate>Fri, 15 May 2026 14:53:33 +0000</pubDate>
      <content:encoded><![CDATA[
        <p><a href="https://www.smallobservations.net/2025/12/london-brown-bird/"><img src="https://foo.smallobservations.net/images/bird.jpg" alt="A brown bird on a wall."></a></p>
      ]]></content:encoded>
    </item>
  </channel>
</rss>
""",
    )
    write(
        public / "sitemap.xml",
        """
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.smallobservations.net/2025/12/london-brown-bird/</loc>
    <lastmod>2026-05-15T14:53:33+00:00</lastmod>
  </url>
</urlset>
""",
    )

    errors = audit_feed_and_sitemap(public, content)

    assert "feed.xml: URL must use apex domain https://smallobservations.net: https://foo.smallobservations.net/feed.xml" in errors
    assert "feed.xml: URL must use apex domain https://smallobservations.net: https://www.smallobservations.net/2025/12/london-brown-bird/" in errors
    assert "feed.xml: URL must use apex domain https://smallobservations.net: https://foo.smallobservations.net/images/bird.jpg" in errors
    assert "sitemap.xml: URL must use apex domain https://smallobservations.net: https://www.smallobservations.net/2025/12/london-brown-bird/" in errors


def test_reports_missing_llms_txt(tmp_path: Path) -> None:
    public = tmp_path / "public"
    content = tmp_path / "content/posts"
    write(
        content / "post.md",
        """
---
slug: "london-brown-bird"
date: 2025-12-04T08:24:43Z
publishDate: 2026-05-15T14:53:33Z
---
""",
    )
    write(
        public / "feed.xml",
        """
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <atom:link href="https://smallobservations.net/feed.xml" rel="self" type="application/rss+xml"/>
    <item>
      <link>https://smallobservations.net/2025/12/london-brown-bird/</link>
      <pubDate>Fri, 15 May 2026 14:53:33 +0000</pubDate>
      <content:encoded><![CDATA[
        <p><a href="https://smallobservations.net/2025/12/london-brown-bird/"><img src="https://smallobservations.net/images/bird.jpg" alt="A brown bird on a wall."></a></p>
      ]]></content:encoded>
    </item>
  </channel>
</rss>
""",
    )
    write(
        public / "sitemap.xml",
        """
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://smallobservations.net/2025/12/london-brown-bird/</loc>
    <lastmod>2026-05-15T14:53:33+00:00</lastmod>
  </url>
</urlset>
""",
    )

    assert audit_feed_and_sitemap(public, content) == ["llms.txt: missing"]


def test_reports_llms_txt_contract_regressions(tmp_path: Path) -> None:
    public = tmp_path / "public"
    content = tmp_path / "content/posts"
    write(
        content / "post.md",
        """
---
slug: "london-brown-bird"
date: 2025-12-04T08:24:43Z
publishDate: 2026-05-15T14:53:33Z
---
""",
    )
    write(
        public / "llms.txt",
        """
# Small Observations draft

> A notebook of street art.

## Core

- [Home](https://www.smallobservations.net/): Wrong hostname.
""",
    )
    write(
        public / "feed.xml",
        """
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <atom:link href="https://smallobservations.net/feed.xml" rel="self" type="application/rss+xml"/>
    <item>
      <link>https://smallobservations.net/2025/12/london-brown-bird/</link>
      <pubDate>Fri, 15 May 2026 14:53:33 +0000</pubDate>
      <content:encoded><![CDATA[
        <p><a href="https://smallobservations.net/2025/12/london-brown-bird/"><img src="https://smallobservations.net/images/bird.jpg" alt="A brown bird on a wall."></a></p>
      ]]></content:encoded>
    </item>
  </channel>
</rss>
""",
    )
    write(
        public / "sitemap.xml",
        """
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://smallobservations.net/2025/12/london-brown-bird/</loc>
    <lastmod>2026-05-15T14:53:33+00:00</lastmod>
  </url>
</urlset>
""",
    )

    errors = audit_feed_and_sitemap(public, content)

    assert "llms.txt: first line must be # Small Observations" in errors
    assert "llms.txt: missing required URL https://smallobservations.net/posts/" in errors
    assert "llms.txt: URL must use apex domain https://smallobservations.net: https://www.smallobservations.net/" in errors


def test_reports_missing_llms_author_link(tmp_path: Path) -> None:
    public = tmp_path / "public"
    content = tmp_path / "content/posts"
    write(
        content / "post.md",
        """
---
slug: "london-brown-bird"
date: 2025-12-04T08:24:43Z
publishDate: 2026-05-15T14:53:33Z
---
""",
    )
    write(
        public / "llms.txt",
        """
# Small Observations

> A notebook of street art I've enjoyed and photographed since 2005, browsable by city, artist, year, and tag.

Small Observations is a static Hugo photo archive. Each post is one photographed artwork or street-art sighting. Post dates are the dates the photos were taken; the RSS feed is ordered by publish date. Alt text describes what is visible in each image.

This file is a navigation aid for agents and readers. It is not a licence grant and does not replace robots.txt.

## Core

- [Home](https://smallobservations.net/): Curated favourite photos and entry points into the archive.
- [Latest posts](https://smallobservations.net/posts/): All photo posts, ordered by photo date.
- [RSS feed](https://smallobservations.net/feed.xml): Newest published posts.
- [Sitemap](https://smallobservations.net/sitemap.xml): Complete indexable URL list.

## Browse the archive

- [Favourites](https://smallobservations.net/tags/favourite/): Selected photos the author keeps coming back to.
- [Tags](https://smallobservations.net/tags/): Subjects, themes, context, and styles.
- [Tags by count](https://smallobservations.net/tags/by-count/): Tags ordered by frequency.
- [Cities](https://smallobservations.net/cities/): Posts grouped by city.
- [Countries](https://smallobservations.net/countries/): Posts grouped by country.
- [Years](https://smallobservations.net/years/): Posts grouped by year photographed.
- [Artists](https://smallobservations.net/artists/): Posts grouped by identified artist.
""",
    )
    write(
        public / "feed.xml",
        """
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <atom:link href="https://smallobservations.net/feed.xml" rel="self" type="application/rss+xml"/>
    <item>
      <link>https://smallobservations.net/2025/12/london-brown-bird/</link>
      <pubDate>Fri, 15 May 2026 14:53:33 +0000</pubDate>
      <content:encoded><![CDATA[
        <p><a href="https://smallobservations.net/2025/12/london-brown-bird/"><img src="https://smallobservations.net/images/bird.jpg" alt="A brown bird on a wall."></a></p>
      ]]></content:encoded>
    </item>
  </channel>
</rss>
""",
    )
    write(
        public / "sitemap.xml",
        """
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://smallobservations.net/2025/12/london-brown-bird/</loc>
    <lastmod>2026-05-15T14:53:33+00:00</lastmod>
  </url>
</urlset>
""",
    )

    errors = audit_feed_and_sitemap(public, content)

    assert "llms.txt: missing required URL https://jonathandeamer.com/" in errors


def test_reports_rss_limit_order_and_reader_image_regressions(tmp_path: Path) -> None:
    public = tmp_path / "public"
    content = tmp_path / "content/posts"
    write_valid_llms_txt(public)
    for index in range(21):
        write(
            content / f"post-{index}.md",
            f"""
---
slug: "post-{index}"
date: 2025-12-{index + 1:02d}T08:24:43Z
publishDate: 2026-05-15T14:53:{59 - index:02d}Z
---
""",
        )

    items = "\n".join(
        f"""
    <item>
      <link>https://smallobservations.net/2025/12/post-{index}/</link>
      <pubDate>Fri, 15 May 2026 14:53:{index:02d} +0000</pubDate>
      <content:encoded><![CDATA[
        <p><a href="https://smallobservations.net/2025/12/post-{index}/"><img src="/images/post-{index}.jpg" alt=""></a></p>
      ]]></content:encoded>
    </item>
"""
        for index in range(21)
    )
    write(
        public / "feed.xml",
        f"""
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <atom:link href="https://smallobservations.net/feed.xml" rel="self" type="application/rss+xml"/>
{items}
  </channel>
</rss>
""",
    )
    write(
        public / "sitemap.xml",
        """
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>
""",
    )

    errors = audit_feed_and_sitemap(public, content)

    assert "feed.xml: RSS feed must contain no more than 20 items" in errors
    assert "feed.xml: RSS items must be ordered by pubDate descending" in errors
    assert "feed.xml: https://smallobservations.net/2025/12/post-0/ content image src must be absolute" in errors
    assert "feed.xml: https://smallobservations.net/2025/12/post-0/ content image must have non-empty alt text" in errors
