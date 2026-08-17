"""RSS manbalardan yangi xabarlarni yig'ib beradi."""
import re
import feedparser
import config


def _extract_image(entry) -> str | None:
    if hasattr(entry, "media_content") and entry.media_content:
        url = entry.media_content[0].get("url")
        if url:
            return url
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        url = entry.media_thumbnail[0].get("url")
        if url:
            return url

    for link in entry.get("links", []):
        if link.get("type", "").startswith("image"):
            return link.get("href")

    html = entry.get("summary", "") or entry.get("description", "")
    match = re.search(r'<img[^>]+src="([^"]+)"', html)
    if match:
        return match.group(1)

    return None


def fetch_rss_items() -> list[dict]:
    items = []
    for source in config.RSS_SOURCES:
        feed_url = source["url"]
        priority = source.get("priority", "primary")
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"[RSS xatosi] {feed_url}: {e}")
            continue

        for entry in feed.entries[:10]:
            uid = entry.get("id") or entry.get("link")
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = f"{title}\n{summary}"
            text_lower = text.lower()

            if any(kw.lower() in text_lower for kw in config.BLOCKED_KEYWORDS):
                continue

            if not any(kw.lower() in text_lower for kw in config.KEYWORDS):
                continue

            items.append({
                "id": f"rss:{uid}",
                "text": text,
                "source": feed_url,
                "image_url": _extract_image(entry),
                "priority": priority,
                "signature": None,
            })
    return items

