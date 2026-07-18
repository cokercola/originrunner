"""
Fetches the latest headlines from a handful of real running-news RSS feeds
and writes the top 4 (by publish date) to data/news.json for the homepage
to render. Run automatically once a day by .github/workflows/update-news.yml
"""

import json
import re
from datetime import datetime, timezone
from time import mktime

import feedparser

FEEDS = [
    {"url": "https://runblogrun.com/feed", "source": "RunBlogRun", "color": "#85B7EB"},
    {"url": "https://trailrunner.com/trail-news/feed", "source": "Trail Runner", "color": "#F0997B"},
    {"url": "https://ultrarunning.com/feed", "source": "UltraRunning Magazine", "color": "#97C459"},
]

MAX_ITEMS = 4
EXCERPT_LEN = 160


def clean_excerpt(summary):
    text = re.sub("<[^<]+?>", "", summary or "").strip()
    if len(text) > EXCERPT_LEN:
        text = text[:EXCERPT_LEN].rsplit(" ", 1)[0] + "..."
    return text


def get_image(entry):
    if getattr(entry, "media_content", None):
        return entry.media_content[0].get("url")
    if getattr(entry, "media_thumbnail", None):
        return entry.media_thumbnail[0].get("url")
    for link in getattr(entry, "links", []):
        if link.get("type", "").startswith("image"):
            return link.get("href")

    for link in getattr(entry, "links", []):
        if link.get("rel") == "enclosure" and link.get("type", "").startswith("image"):
            return link.get("href")

    html_blobs = []
    if entry.get("summary"):
        html_blobs.append(entry.get("summary"))
    if entry.get("content"):
        for c in entry.get("content"):
            if c.get("value"):
                html_blobs.append(c.get("value"))

    for blob in html_blobs:
        match = re.search(r'<img[^>]+src="([^"]+)"', blob)
        if match:
            return match.group(1)

    return None


def main():
    items = []
    for feed in FEEDS:
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries[:5]:
            pub = entry.get("published_parsed") or entry.get("updated_parsed")
            pub_dt = (
                datetime.fromtimestamp(mktime(pub), tz=timezone.utc)
                if pub
                else datetime.now(timezone.utc)
            )
            items.append(
                {
                    "title": entry.get("title", "Untitled"),
                    "link": entry.get("link", "#"),
                    "excerpt": clean_excerpt(entry.get("summary", "")),
                    "source": feed["source"],
                    "source_color": feed["color"],
                    "date": pub_dt.strftime("%b %d, %Y").upper(),
                    "timestamp": pub_dt.isoformat(),
                    "image": get_image(entry),
                }
            )

    items.sort(key=lambda x: x["timestamp"], reverse=True)
    items = items[:MAX_ITEMS]

    output = {"updated": datetime.now(timezone.utc).isoformat(), "items": items}

    with open("data/news.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(items)} headlines to data/news.json")


if __name__ == "__main__":
    main()
