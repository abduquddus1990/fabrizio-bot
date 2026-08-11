"""
Agar manba xabarida rasm bo'lmasa, futbolchining ismi bo'yicha
Wikipedia'dan (bepul, ochiq API) mos rasmni qidiradi.
"""
import urllib.parse
import requests

SEARCH_URL = "https://en.wikipedia.org/w/api.php"
SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"


def _search_title(name: str) -> str | None:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"{name} footballer",
        "format": "json",
        "srlimit": 1,
    }
    try:
        resp = requests.get(SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("query", {}).get("search", [])
        if results:
            return results[0]["title"]
    except Exception:
        pass
    return None


def get_player_photo(player_name: str | None) -> str | None:
    if not player_name:
        return None

    title = _search_title(player_name) or player_name

    try:
        url = SUMMARY_URL.format(urllib.parse.quote(title))
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        thumbnail = data.get("thumbnail") or data.get("originalimage") or {}
        return thumbnail.get("source")
    except Exception as e:
        print(f"[Wikipedia rasm qidirish xatosi] {player_name}: {e}")
        return None
