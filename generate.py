
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

    for item in items:
        title = html.escape(item["title"])
        link = html.escape(item["link"], quote=True)
        description = html.escape(item["description"])
        pub_date = html.escape(item["pub_date"])
        image = html.escape(item["image"], quote=True)

        image_html = (
            f'<img src="{image}" alt="{title}" loading="lazy">'
            if image else ""
        )

        cards.append(f"""
        <article class="post">
            {image_html}
            <div class="post-content">
                <p class="date">{pub_date}</p>
                <h2><a href="{link}" target="_blank" rel="noopener">{title}</a></h2>
                <p>{description}</p>
                <a class="read-more" href="{link}" target="_blank" rel="noopener">
                    Read article →
                </a>
            </div>
        </article>
        """)

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

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
<style>
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f5f7fa;
    color: #263238;
    line-height: 1.6;
}}
header {{
    background: #173c55;
    color: white;
    padding: 45px 20px;
    text-align: center;
}}
header h1 {{ margin: 0 0 10px; }}
.container {{
    max-width: 1000px;
    margin: 35px auto;
    padding: 0 18px;
}}
.search {{
    width: 100%;
    padding: 14px;
    margin-bottom: 25px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 16px;
}}
.post {{
    display: flex;
    gap: 20px;
    background: white;
    padding: 20px;
    margin-bottom: 18px;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,.05);
}}
.post img {{
    width: 220px;
    height: 150px;
    object-fit: cover;
    border-radius: 7px;
}}
.post-content {{ flex: 1; min-width: 0; }}
.post h2 {{ margin: 5px 0 10px; font-size: 21px; }}
.post h2 a {{ color: #173c55; text-decoration: none; }}
.post h2 a:hover {{ color: #d18a35; }}
.date {{ color: #888; font-size: 13px; }}
.read-more {{ color: #b66c23; font-weight: bold; }}
footer {{
    text-align: center;
    padding: 30px;
    color: #777;
}}
@media(max-width:600px) {{
    .post {{ display: block; }}
    .post img {{ width: 100%; height: 200px; }}
}}
</style>
</head>
<body>
<header>
    <h1>{html.escape(SITE_TITLE)}</h1>
    <p>{html.escape(SITE_DESCRIPTION)}</p>
</header>
<main class="container">
    <input class="search" id="search" type="search"
           placeholder="Search articles...">
    <p>Latest articles: {len(items)}</p>
    <section id="posts">
        {''.join(cards)}
    </section>
</main>
<footer>
    <p>Last synchronized: {updated}</p>
    <p><a href="./feed.xml">RSS Feed</a></p>
    <p>Original articles by Point Booking</p>
</footer>
<script>
document.getElementById("search").addEventListener("input", function() {{
    const query = this.value.toLowerCase();
    document.querySelectorAll(".post").forEach(post => {{
        post.style.display = post.innerText.toLowerCase().includes(query)
            ? "" : "none";
    }});
}});
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
