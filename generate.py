
import urllib.request
import xml.etree.ElementTree as ET
import html
import re
import os
from datetime import datetime, timezone
from email.utils import format_datetime
from html.parser import HTMLParser

RSS_URL = "https://www.pointbookingofficial.com/feeds/posts/default?alt=rss&max-results=100"
SITE_TITLE = "Point Booking - Latest Articles"
SITE_DESCRIPTION = "Latest travel articles from Point Booking."
SITE_URL = os.environ.get(
    "GITHUB_PAGES_URL",
    "https://YOUR_USERNAME.github.io/pointbooking-rss"
)

OUTPUT_DIR = "public"
MAX_ITEMS = 100


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts)


def clean_html(value):
    parser = TextExtractor()
    try:
        parser.feed(value or "")
        return re.sub(r"\s+", " ", parser.get_text()).strip()
    except Exception:
        return value or ""


def get_image(item):
    # Blogger media:thumbnail
    for element in item.iter():
        if element.tag.endswith("thumbnail"):
            url = element.attrib.get("url")
            if url:
                return url

    # RSS enclosure
    for element in item.findall("enclosure"):
        if element.attrib.get("type", "").startswith("image/"):
            return element.attrib.get("url", "")

    # Image embedded in description/content
    for element in item.iter():
        if element.tag.endswith(("encoded", "description")):
            content = element.text or ""
            match = re.search(
                r'<img[^>]+src=["\']([^"\']+)["\']',
                content,
                re.IGNORECASE
            )
            if match:
                return match.group(1)

    return ""


def get_text(item, tag):
    element = item.find(tag)
    return element.text.strip() if element is not None and element.text else ""


def fetch_rss():
    request = urllib.request.Request(
        RSS_URL,
        headers={"User-Agent": "PointBookingRSSBot/1.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()

    root = ET.fromstring(data)
    items = []

    # RSS 2.0
    for item in root.findall(".//item"):
        title = get_text(item, "title")
        link = get_text(item, "link")
        description = get_text(item, "description")
        pub_date = get_text(item, "pubDate")

        if not title or not link:
            continue

        items.append({
            "title": title,
            "link": link,
            "description": clean_html(description)[:500],
            "pub_date": pub_date,
            "image": get_image(item)
        })

    # Atom fallback
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall(".//atom:entry", ns):
            title = entry.findtext("atom:title", default="", namespaces=ns)
            link_element = entry.find("atom:link", ns)
            link = link_element.attrib.get("href", "") if link_element is not None else ""
            summary = entry.findtext("atom:summary", default="", namespaces=ns)
            published = entry.findtext("atom:published", default="", namespaces=ns)

            if title and link:
                items.append({
                    "title": title,
                    "link": link,
                    "description": clean_html(summary)[:500],
                    "pub_date": published,
                    "image": get_image(entry)
                })

    # Remove duplicate URLs
    unique = {}
    for item in items:
        unique[item["link"]] = item

    return list(unique.values())[:MAX_ITEMS]



def generate_html(items):
    cards = []

    for index, item in enumerate(items):
        title = html.escape(item["title"])
        link = html.escape(item["link"], quote=True)
        description = html.escape(item["description"])
        pub_date = html.escape(item["pub_date"])
        image = html.escape(item["image"], quote=True)

        image_html = (
            f'<img src="{image}" alt="{title}" loading="lazy">'
            if image else '<div class="post-placeholder">POINT BOOKING</div>'
        )

        featured = " featured" if index == 0 else ""

        cards.append(f"""
        <article class="post{featured}">
            <a class="post-image" href="{link}" target="_blank" rel="noopener">
                {image_html}
            </a>

            <div class="post-content">
                <span class="post-category">
                    {"FEATURED ARTICLE" if index == 0 else "TRAVEL & DISCOVER"}
                </span>

                <p class="date">{pub_date}</p>

                <h2>
                    <a href="{link}" target="_blank" rel="noopener">
                        {title}
                    </a>
                </h2>

                <p class="description">{description}</p>

                <a class="read-more" href="{link}"
                   target="_blank" rel="noopener">
                    Read Article <span>↗</span>
                </a>
            </div>
        </article>
        """)

    updated = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{html.escape(SITE_TITLE)}</title>

<meta name="description" content="{html.escape(SITE_DESCRIPTION)}">
<meta name="robots" content="index,follow">

<link rel="alternate" type="application/rss+xml"
      title="Point Booking RSS" href="./feed.xml">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@500;600;700&display=swap"
      rel="stylesheet">

<style>
:root {
    --navy: #102b3b;
    --gold: #c49a60;
    --cream: #f7f6f2;
    --white: #ffffff;
    --text: #253440;
    --muted: #84909a;
    --border: #e9e8e3;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    scroll-behavior: smooth;
}

body {
    font-family: 'DM Sans', sans-serif;
    background: var(--cream);
    color: var(--text);
    line-height: 1.7;
}

/* HEADER */

.topbar {
    background: var(--navy);
    color: white;
    padding: 13px 5%;
}

.topbar-inner {
    max-width: 1240px;
    margin: auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 15px;
}

.brand {
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 2px;
    color: white;
    text-decoration: none;
}

.brand span {
    color: var(--gold);
}

.top-nav {
    display: flex;
    gap: 25px;
    align-items: center;
}

.top-nav a {
    color: #d8e0e5;
    text-decoration: none;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.top-nav a:hover {
    color: var(--gold);
}

/* HERO */

.hero {
    background:
        linear-gradient(120deg, rgba(9,32,46,.97), rgba(16,43,59,.85)),
        radial-gradient(circle at 80% 30%, #54717c, #102b3b);
    color: white;
    padding: 85px 20px 90px;
    text-align: center;
}

.hero-inner {
    max-width: 850px;
    margin: auto;
}

.hero-label {
    color: var(--gold);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 20px;
}

.hero h1 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(36px, 6vw, 65px);
    font-weight: 600;
    line-height: 1.2;
    margin-bottom: 20px;
}

.hero h1 span {
    color: #d5b17e;
}

.hero-description {
    color: #d2dce1;
    max-width: 600px;
    margin: auto;
    font-size: 15px;
}

.hero-divider {
    width: 55px;
    height: 2px;
    background: var(--gold);
    margin: 30px auto 0;
}

/* MAIN */

.container {
    max-width: 1200px;
    margin: auto;
    padding: 65px 25px 85px;
}

.section-heading {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 20px;
    margin-bottom: 30px;
}

.section-label {
    color: var(--gold);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.section-heading h2 {
    font-family: 'Playfair Display', serif;
    font-size: 34px;
    font-weight: 600;
    color: var(--navy);
}

.article-count {
    color: var(--muted);
    font-size: 13px;
    white-space: nowrap;
}

/* SEARCH */

.search-wrap {
    position: relative;
    margin-bottom: 35px;
}

.search-wrap input {
    width: 100%;
    padding: 17px 20px 17px 50px;
    border: 1px solid var(--border);
    border-radius: 5px;
    background: white;
    font-family: inherit;
    font-size: 14px;
    outline: none;
    transition: .25s;
}

.search-wrap input:focus {
    border-color: var(--gold);
    box-shadow: 0 0 0 3px rgba(196,154,96,.12);
}

.search-icon {
    position: absolute;
    left: 19px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--muted);
    font-size: 19px;
}

/* ARTICLE GRID */

.posts-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 28px;
}

.post {
    background: white;
    border: 1px solid var(--border);
    border-radius: 7px;
    overflow: hidden;
    transition: transform .3s, box-shadow .3s;
    min-width: 0;
}

.post:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 35px rgba(16,43,59,.09);
}

.post-image {
    display: block;
    width: 100%;
    height: 230px;
    overflow: hidden;
    background: #e9eceb;
}

.post-image img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform .6s;
}

.post:hover .post-image img {
    transform: scale(1.05);
}

.post-placeholder {
    width: 100%;
    height: 100%;
    display: grid;
    place-items: center;
    background: var(--navy);
    color: var(--gold);
    letter-spacing: 3px;
    font-weight: 800;
}

.post-content {
    padding: 25px 27px 28px;
}

.post-category {
    display: inline-block;
    color: var(--gold);
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 10px;
}

.date {
    color: var(--muted);
    font-size: 11px;
    margin-bottom: 9px;
}

.post h2 {
    font-family: 'Playfair Display', serif;
    font-size: 23px;
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: 13px;
}

.post h2 a {
    color: var(--navy);
    text-decoration: none;
}

.post h2 a:hover {
    color: #b58951;
}

.description {
    font-size: 13px;
    color: #77828a;
    line-height: 1.8;
    margin-bottom: 20px;
}

.read-more {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    color: var(--navy);
    text-decoration: none;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.read-more span {
    color: var(--gold);
    font-size: 17px;
    transition: transform .2s;
}

.read-more:hover span {
    transform: translate(3px, -3px);
}

/* FEATURED ARTICLE */

.post.featured {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: 1.15fr 1fr;
    min-height: 350px;
}

.post.featured .post-image {
    height: 100%;
    min-height: 350px;
}

.post.featured .post-content {
    align-self: center;
    padding: 40px;
}

.post.featured h2 {
    font-size: clamp(25px, 3vw, 34px);
}

.post.featured .description {
    font-size: 14px;
}

/* NO RESULTS */

.no-results {
    display: none;
    text-align: center;
    padding: 50px 15px;
    color: var(--muted);
    background: white;
    border: 1px solid var(--border);
    border-radius: 6px;
}

/* FOOTER */

footer {
    background: var(--navy);
    color: #cbd5db;
    padding: 55px 20px 30px;
    text-align: center;
}

.footer-brand {
    font-family: 'Playfair Display', serif;
    font-size: 28px;
    color: white;
    margin-bottom: 10px;
}

.footer-brand span {
    color: var(--gold);
}

footer p {
    font-size: 12px;
    margin-bottom: 12px;
}

.footer-links {
    display: flex;
    justify-content: center;
    gap: 25px;
    flex-wrap: wrap;
    margin: 25px 0;
}

.footer-links a {
    color: #d8c19e;
    text-decoration: none;
    font-size: 12px;
}

.footer-bottom {
    border-top: 1px solid rgba(255,255,255,.12);
    padding-top: 22px;
    margin-top: 25px;
    color: #91a1aa;
    font-size: 11px;
}

/* RESPONSIVE */

@media (max-width: 768px) {
    .hero {
        padding: 65px 20px;
    }

    .container {
        padding: 45px 18px 60px;
    }

    .posts-grid {
        grid-template-columns: 1fr;
        gap: 20px;
    }

    .post.featured {
        grid-column: auto;
        grid-template-columns: 1fr;
    }

    .post.featured .post-image {
        min-height: 230px;
        height: 230px;
    }

    .post.featured .post-content {
        padding: 25px;
    }

    .post.featured h2 {
        font-size: 25px;
    }

    .section-heading h2 {
        font-size: 28px;
    }

    .top-nav {
        gap: 12px;
    }

    .top-nav a {
        font-size: 10px;
    }
}

@media (max-width: 420px) {
    .topbar {
        padding: 13px 15px;
    }

    .brand {
        font-size: 14px;
    }

    .top-nav a {
        font-size: 9px;
    }

    .hero h1 {
        font-size: 37px;
    }

    .section-heading {
        align-items: start;
        flex-direction: column;
    }

    .post-content {
        padding: 22px;
    }

    .post h2 {
        font-size: 21px;
    }
}
</style>
</head>

<body>

<!-- HEADER -->

<div class="topbar">
    <div class="topbar-inner">
        <a href="./" class="brand">
            POINT<span>BOOKING</span>
        </a>

        <nav class="top-nav">
            <a href="./">Home</a>
            <a href="#articles">Articles</a>
            <a href="./feed.xml">RSS Feed ↗</a>
        </nav>
    </div>
</div>

<!-- HERO -->

<header class="hero">
    <div class="hero-inner">
        <p class="hero-label">Travel · Explore · Discover</p>

        <h1>
            Discover the World<br>
            <span>One Journey at a Time.</span>
        </h1>

        <p class="hero-description">
            Discover inspiring travel stories, beautiful destinations
            and unforgettable experiences with Point Booking.
        </p>

        <div class="hero-divider"></div>
    </div>
</header>

<!-- MAIN CONTENT -->

<main class="container" id="articles">

    <div class="section-heading">
        <div>
            <p class="section-label">Our Journal</p>
            <h2>Latest Stories</h2>
        </div>

        <p class="article-count">
            {len(items)} Articles · Updated {updated}
        </p>
    </div>

    <div class="search-wrap">
        <span class="search-icon">⌕</span>
        <input
            type="search"
            id="search"
            placeholder="Search destinations, stories and articles..."
            aria-label="Search articles">
    </div>

    <section class="posts-grid" id="posts">
        {''.join(cards)}
    </section>

    <div class="no-results" id="noResults">
        <h3>No articles found</h3>
        <p>Try another keyword to discover more stories.</p>
    </div>

</main>

<!-- FOOTER -->

<footer>
    <div class="footer-brand">
        POINT<span>BOOKING</span>
    </div>

    <p>
        Discover beautiful destinations and inspiring travel stories.
    </p>

    <div class="footer-links">
        <a href="./">Home</a>
        <a href="#articles">Latest Articles</a>
        <a href="./feed.xml">RSS Feed</a>
        <a href="https://www.pointbookingofficial.com/"
           target="_blank" rel="noopener">
            Official Website ↗
        </a>
    </div>

    <div class="footer-bottom">
        <p>Last synchronized: {updated}</p>
        <p>© {datetime.now(timezone.utc).year} Point Booking. All rights reserved.</p>
    </div>
</footer>

<!-- SEARCH SCRIPT -->

<script>
(function() {
    const search = document.getElementById("search");
    const posts = document.querySelectorAll(".post");
    const noResults = document.getElementById("noResults");

    search.addEventListener("input", function() {
        const query = this.value.toLowerCase().trim();
        let visible = 0;

        posts.forEach(function(post) {
            const match = post.innerText.toLowerCase().includes(query);

            post.style.display = match ? "" : "none";

            if (match) visible++;
        });

        noResults.style.display = visible === 0 ? "block" : "none";
    });
})();
</script>

</body>
</html>"""


def generate_feed(items):
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")

    ET.SubElement(channel, "title").text = SITE_TITLE
    ET.SubElement(channel, "link").text = SITE_URL
    ET.SubElement(channel, "description").text = SITE_DESCRIPTION
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(
        datetime.now(timezone.utc)
    )

    for item in items:
        element = ET.SubElement(channel, "item")
        ET.SubElement(element, "title").text = item["title"]
        ET.SubElement(element, "link").text = item["link"]
        ET.SubElement(element, "guid").text = item["link"]
        ET.SubElement(element, "description").text = item["description"]

        if item["pub_date"]:
            ET.SubElement(element, "pubDate").text = item["pub_date"]

    return ET.ElementTree(root)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Fetching Blogger RSS...")
    items = fetch_rss()

    print(f"Found {len(items)} articles.")

    if not items:
        raise RuntimeError("No articles found. Keeping deployment from failing.")

    html_content = generate_html(items)

    with open(f"{OUTPUT_DIR}/index.html", "w", encoding="utf-8") as file:
        file.write(html_content)

    feed = generate_feed(items)
    feed.write(
        f"{OUTPUT_DIR}/feed.xml",
        encoding="utf-8",
        xml_declaration=True
    )

    print("Website generated successfully.")


if __name__ == "__main__":
    main()
