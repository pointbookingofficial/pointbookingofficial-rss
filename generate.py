
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

    return  return f"""<!DOCTYPE html>
<html lang="vi">
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
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {{
    --bg: #f2f5f8;
    --surface: #ffffff;
    --ink: #10242f;
    --muted: #64768a;
    --line: #e2e8ee;
    --brand: #0b3a55;
    --brand-2: #0f6b8f;
    --accent: #f08a24;
    --accent-ink: #b45f0c;
    --shadow: 0 1px 2px rgba(16,36,47,.06), 0 8px 24px rgba(16,36,47,.06);
    --shadow-hover: 0 2px 4px rgba(16,36,47,.08), 0 16px 36px rgba(16,36,47,.12);
}}
@media (prefers-color-scheme: dark) {{
    :root {{
        --bg: #0b1520;
        --surface: #12202e;
        --ink: #e8eff5;
        --muted: #8ea2b4;
        --line: #1f3244;
        --accent-ink: #ffa94d;
        --shadow: 0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.3);
        --shadow-hover: 0 2px 4px rgba(0,0,0,.5), 0 16px 36px rgba(0,0,0,.45);
    }}
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
    margin: 0;
    font-family: "Be Vietnam Pro", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
    background: var(--bg);
    color: var(--ink);
    line-height: 1.65;
    -webkit-font-smoothing: antialiased;
}}
a {{ color: inherit; }}
:focus-visible {{ outline: 3px solid var(--accent); outline-offset: 3px; border-radius: 6px; }}

/* ---------- Header ---------- */
.hero {{
    background:
        radial-gradient(900px 300px at 85% -10%, rgba(240,138,36,.28), transparent 60%),
        linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 100%);
    color: #fff;
    padding: 64px 20px 110px;
}}
.hero-inner {{ max-width: 1120px; margin: 0 auto; }}
.hero h1 {{
    margin: 0 0 14px;
    font-size: clamp(32px, 5.5vw, 56px);
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.02em;
    max-width: 18ch;
}}
.hero p {{
    margin: 0;
    max-width: 56ch;
    font-size: clamp(16px, 2vw, 19px);
    color: rgba(255,255,255,.82);
}}

/* ---------- Search ---------- */
.search-wrap {{
    max-width: 1120px;
    margin: -34px auto 0;
    padding: 0 20px;
    position: relative;
    z-index: 2;
}}
.search-box {{
    display: flex;
    align-items: center;
    gap: 12px;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 0 18px;
    box-shadow: var(--shadow-hover);
}}
.search-box svg {{ flex: none; color: var(--muted); }}
.search {{
    flex: 1;
    min-width: 0;
    border: 0;
    background: transparent;
    color: var(--ink);
    font: inherit;
    font-size: 17px;
    padding: 18px 0;
}}
.search:focus {{ outline: none; }}
.search-box:focus-within {{ border-color: var(--accent); box-shadow: 0 0 0 4px rgba(240,138,36,.2), var(--shadow-hover); }}
.search::placeholder {{ color: var(--muted); }}

/* ---------- Layout ---------- */
.container {{ max-width: 1120px; margin: 0 auto; padding: 28px 20px 60px; }}
.meta-row {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 22px;
    color: var(--muted);
    font-size: 14px;
}}
.meta-row strong {{ color: var(--ink); }}

.posts {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
}}

/* ---------- Cards ---------- */
.post {{
    display: flex;
    flex-direction: column;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 18px;
    overflow: hidden;
    box-shadow: var(--shadow);
    transition: transform .25s ease, box-shadow .25s ease;
}}
.post:hover {{ transform: translateY(-4px); box-shadow: var(--shadow-hover); }}
.thumb {{ display: block; aspect-ratio: 16 / 10; overflow: hidden; background: var(--line); }}
.thumb img, .thumb-fallback {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    transition: transform .5s ease;
}}
.thumb-fallback {{ background: linear-gradient(135deg, var(--brand), var(--brand-2)); }}
.post:hover .thumb img {{ transform: scale(1.05); }}
.post-content {{ display: flex; flex-direction: column; flex: 1; padding: 20px 22px 22px; min-width: 0; }}
.date {{ color: var(--muted); font-size: 13px; }}
.post h2 {{
    margin: 6px 0 10px;
    font-size: 19px;
    line-height: 1.35;
    font-weight: 700;
    letter-spacing: -0.01em;
}}
.post h2 a {{ text-decoration: none; }}
.post h2 a:hover {{ color: var(--brand-2); }}
.summary {{
    margin: 0 0 16px;
    color: var(--muted);
    font-size: 15px;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}
.read-more {{
    margin-top: auto;
    align-self: flex-start;
    color: var(--accent-ink);
    font-weight: 600;
    font-size: 14px;
    text-decoration: none;
    border-bottom: 2px solid transparent;
}}
.read-more:hover {{ border-bottom-color: currentColor; }}

/* Bài đầu tiên nổi bật (chỉ khi chưa tìm kiếm) */
.posts.idle .post:first-child {{
    grid-column: 1 / -1;
    flex-direction: row;
}}
.posts.idle .post:first-child .thumb {{ flex: 1.2; aspect-ratio: auto; min-height: 320px; }}
.posts.idle .post:first-child .post-content {{ flex: 1; justify-content: center; padding: 36px; }}
.posts.idle .post:first-child h2 {{ font-size: clamp(24px, 3vw, 32px); line-height: 1.2; }}
.posts.idle .post:first-child .summary {{ font-size: 16px; -webkit-line-clamp: 4; }}

.empty {{
    display: none;
    text-align: center;
    padding: 60px 20px;
    color: var(--muted);
}}
.empty strong {{ display: block; color: var(--ink); font-size: 18px; margin-bottom: 6px; }}

/* ---------- Footer ---------- */
footer {{
    border-top: 1px solid var(--line);
    padding: 32px 20px 44px;
    text-align: center;
    color: var(--muted);
    font-size: 14px;
}}
footer p {{ margin: 4px 0; }}
footer a {{ color: var(--accent-ink); font-weight: 600; text-decoration: none; }}
footer a:hover {{ text-decoration: underline; }}

/* ---------- Responsive ---------- */
@media (max-width: 900px) {{
    .posts {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 640px) {{
    .hero {{ padding: 44px 18px 96px; }}
    .posts {{ grid-template-columns: 1fr; gap: 18px; }}
    .posts.idle .post:first-child {{ flex-direction: column; }}
    .posts.idle .post:first-child .thumb {{ min-height: 0; aspect-ratio: 16 / 10; flex: none; }}
    .posts.idle .post:first-child .post-content {{ padding: 20px 22px 22px; }}
}}
@media (prefers-reduced-motion: reduce) {{
    * {{ transition: none !important; scroll-behavior: auto !important; }}
}}
</style>
</head>
<body>
<header class="hero">
    <div class="hero-inner">
        <h1>{html.escape(SITE_TITLE)}</h1>
        <p>{html.escape(SITE_DESCRIPTION)}</p>
    </div>
</header>

<div class="search-wrap">
    <label class="search-box">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="7"></circle><path d="m20 20-3.5-3.5"></path>
        </svg>
        <span class="sr-only" style="position:absolute;left:-9999px">Tìm bài viết</span>
        <input class="search" id="search" type="search" autocomplete="off"
               placeholder="Tìm bài viết theo tiêu đề hoặc nội dung">
    </label>
</div>

<main class="container">
    <div class="meta-row">
        <span id="count"><strong>{len(items)}</strong> bài viết mới nhất</span>
        <span>Cập nhật: {updated}</span>
    </div>
    <section class="posts idle" id="posts">
        {''.join(cards)}
    </section>
    <div class="empty" id="empty">
        <strong>Không tìm thấy bài viết nào</strong>
        Thử từ khóa ngắn hơn hoặc kiểm tra lại chính tả.
    </div>
</main>

<footer>
    <p><a href="./feed.xml">Đăng ký RSS</a></p>
    <p>Bài viết gốc của Point Booking</p>
</footer>

<script>
(function() {{
    const input = document.getElementById("search");
    const posts = document.getElementById("posts");
    const empty = document.getElementById("empty");
    const count = document.getElementById("count");
    const cards = Array.from(posts.querySelectorAll(".post"));
    const total = cards.length;

    function normalize(s) {{
        return s.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").replace(/đ/g, "d");
    }}
    const index = cards.map(c => normalize(c.innerText));

    input.addEventListener("input", function() {{
        const q = normalize(this.value.trim());
        let shown = 0;
        cards.forEach((card, i) => {{
            const match = !q || index[i].includes(q);
            card.style.display = match ? "" : "none";
            if (match) shown++;
        }});
        posts.classList.toggle("idle", !q);
        empty.style.display = shown ? "none" : "block";
        count.innerHTML = q
            ? "<strong>" + shown + "</strong> kết quả"
            : "<strong>" + total + "</strong> bài viết mới nhất";
    }});
}})();
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
