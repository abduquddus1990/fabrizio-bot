"""
Fabrizio Romano Bot - bosh boshqaruv skripti.
"""
import os
import sys
import time
import re

# Windows konsolida UTF-8 va emojilarni xatosiz chiqarish
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import config

from rss_reader import fetch_rss_items
from telegram_reader import fetch_telegram_items
from translator import translate_and_format
from poster import post_to_channel
from storage import load_state, save_state
from image_fallback import get_player_photo


def _normalize_text(text: str) -> str:
    """O'xshashlikni solishtirish uchun matnni tozalaydi."""
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def _is_duplicate_title(sarlavha: str, state: dict, window_seconds: int) -> bool:
    """So'nggi vaqt ichida aynan bir xil yoki deyarli bir xil sarlavhali post chiqarilganmi?"""
    if not sarlavha:
        return False
    now = time.time()
    norm_new = _normalize_text(sarlavha)
    
    for old_title, posted_at in state.get("posted_titles", {}).items():
        if (now - posted_at) < window_seconds:
            norm_old = _normalize_text(old_title)
            if norm_new == norm_old:
                return True
            # Agar sarlavhalar juda o'xshash bo'lsa (90%+ moslik)
            words_new = set(norm_new.split())
            words_old = set(norm_old.split())
            if words_new and words_old:
                intersection = words_new.intersection(words_old)
                union = words_new.union(words_old)
                if len(intersection) / len(union) >= 0.85:
                    return True
    return False


def _mark_title_posted(sarlavha: str, state: dict):
    if sarlavha:
        state["posted_titles"][sarlavha] = time.time()


def _finalize_post(item: dict, result: dict, state: dict, forced_manba: str | None = None) -> bool:
    """Tayyor tarjimani postlaydi, state'ni yangilaydi. Muvaffaqiyatni qaytaradi."""
    post_text = result["telegram_post"]

    if item.get("signature") and not forced_manba:
        post_text += f"\n\n© <i>{item['signature']}</i>"

    image_url = item.get("image_url")
    image_bytes = item.get("image_bytes")
    if not image_url and not image_bytes:
        players = result.get("futbolchilar") or []
        if players:
            image_url = get_player_photo(players[0])
            if image_url:
                print(f"[Wikipedia] Rasm topildi: {players[0]}")

    success = post_to_channel(post_text, image_url=image_url, image_bytes=image_bytes)
    if success:
        print(f"[Postlandi] {result['sarlavha']}")
        state["posted_ids"].append(item["id"])
        state["last_post_at"] = time.time()
        _mark_title_posted(result["sarlavha"], state)
        save_state(state)
    else:
        print(f"[Xato] Postlanmadi: {item['id']}")
    return success


def run_once():
    state = load_state()
    now = time.time()
    channel_username = (config.TARGET_CHANNEL or "").lstrip("@")

    all_items = fetch_rss_items() + fetch_telegram_items()
    new_items = [item for item in all_items if item["id"] not in state["posted_ids"]]

    catchup_mode = os.getenv("CATCHUP_MODE", "false").lower() == "true"
    if catchup_mode:
        for item in new_items:
            state["posted_ids"].append(item["id"])
        print(f"[Catchup] {len(new_items)} ta eski xabar postlamasdan 'ko'rilgan' deb belgilandi.")
        save_state(state)
        return

    primary_items = [i for i in new_items if i.get("priority", "primary") == "primary"]
    secondary_items = [i for i in new_items if i.get("priority") == "secondary"]

    if new_items:
        print(f"[Info] Yangi xabarlar: {len(new_items)} (primary: {len(primary_items)}, secondary: {len(secondary_items)})")

    # ---------- 1) PRIMARY manbalar ----------
    for item in primary_items:
        wait_left = config.POST_INTERVAL_SECONDS - (time.time() - state.get("last_post_at", 0))
        if wait_left > 0:
            time.sleep(wait_left)

        try:
            result = translate_and_format(item["text"], channel_username, forced_manba=item.get("forced_manba"))
        except Exception as e:
            print(f"[Xato - tarjima] {item['id']}: {e}")
            continue

        if result is None:
            # Agar xabar transferga aloqasiz bo'lsa yoki reklama bo'lsa, qayta ko'rilmasligi uchun posted_ids ga qo'shamiz
            state["posted_ids"].append(item["id"])
            save_state(state)
            continue

        if _is_duplicate_title(result["sarlavha"], state, config.DUPLICATE_WINDOW_SECONDS):
            print(f"[Info] '{result['sarlavha']}' sarlavhasi bo'yicha dublikat o'tkazib yuborildi")
            state["posted_ids"].append(item["id"])
            save_state(state)
            continue

        _finalize_post(item, result, state, forced_manba=item.get("forced_manba"))

    # ---------- 2) SECONDARY manbalar ----------
    for item in secondary_items:
        first_seen = state["pending"].get(item["id"])

        if first_seen is None:
            state["pending"][item["id"]] = now
            continue

        if (now - first_seen) < config.SECONDARY_HOLD_SECONDS:
            continue

        try:
            result = translate_and_format(item["text"], channel_username, forced_manba="Fabrizio Romano")
        except Exception as e:
            print(f"[Xato - tarjima secondary] {item['id']}: {e}")
            continue

        if result is None:
            state["posted_ids"].append(item["id"])
            state["pending"].pop(item["id"], None)
            save_state(state)
            continue

        if _is_duplicate_title(result["sarlavha"], state, config.SECONDARY_HOLD_SECONDS):
            print(f"[Info] '{result['sarlavha']}' haqida post bor - secondary o'tkazib yuborildi")
            state["posted_ids"].append(item["id"])
            state["pending"].pop(item["id"], None)
            save_state(state)
            continue

        if (time.time() - state.get("last_post_at", 0)) < config.POST_INTERVAL_SECONDS:
            continue

        if _finalize_post(item, result, state, forced_manba="Fabrizio Romano"):
            state["pending"].pop(item["id"], None)
        time.sleep(3)

    save_state(state)


def main():
    loop_mode = "--loop" in sys.argv or "-l" in sys.argv
    if loop_mode:
        print(f"=== Fabrizio Romano Bot doimiy (LOOP) rejimida ishga tushdi ===")
        print(f"Kanal: {config.TARGET_CHANNEL}")
        print(f"Interval: har {config.POLL_INTERVAL_SECONDS} soniyada tekshiriladi.")
        print(f"To'xtatish uchun Ctrl + C bosing.\n")
        try:
            while True:
                run_once()
                time.sleep(config.POLL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\n[Bot to'xtatildi]. Xayr!")
    else:
        run_once()


if __name__ == "__main__":
    main()

