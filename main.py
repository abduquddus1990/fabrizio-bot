"""
Fabrizio Romano Bot - bosh skript.
"""
import os
import time
import config
from rss_reader import fetch_rss_items
from telegram_reader import fetch_telegram_items
from translator import translate_and_format
from poster import post_to_channel
from storage import load_state, save_state
from image_fallback import get_player_photo


def _can_post_now(state: dict) -> bool:
    return (time.time() - state.get("last_post_at", 0)) >= config.POST_INTERVAL_SECONDS


def _players_of(result: dict) -> list[str]:
    """Post ichidagi barcha futbolchi ismlarini kichik harfda, tozalab qaytaradi."""
    return [p.strip().lower() for p in (result.get("futbolchilar") or []) if p and p.strip()]


def _is_duplicate(result: dict, state: dict, window_seconds: int) -> str | None:
    """Agar ro'yxatdagi futbolchilardan BIRORTASI yaqinda postlangan bo'lsa, o'sha ismni qaytaradi."""
    now = time.time()
    for player in _players_of(result):
        posted_at = state["posted_players"].get(player)
        if posted_at and (now - posted_at) < window_seconds:
            return player
    return None


def _mark_players_posted(result: dict, state: dict):
    now = time.time()
    for player in _players_of(result):
        state["posted_players"][player] = now


def _finalize_post(item, result, state, forced_manba=None) -> bool:
    """Tayyor tarjimani postlaydi, state'ni yangilaydi. Muvaffaqiyatni qaytaradi."""
    post_text = result["telegram_post"]

    if item.get("signature") and not forced_manba:
        post_text += f"\n\n© _{item['signature']}_"

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
        _mark_players_posted(result, state)
        # Har bir postdan keyin darhol saqlaymiz - keyinroq jarayon qulasa/vaqt
        # tugasa ham, allaqachon postlangan narsa qayta postlanmasin.
        save_state(state)
    else:
        print(f"[Xato] Postlanmadi: {item['id']}")
    return success


def run_once():
    state = load_state()
    now = time.time()
    channel_username = config.TARGET_CHANNEL.lstrip("@")

    all_items = fetch_rss_items() + fetch_telegram_items()
    new_items = [item for item in all_items if item["id"] not in state["posted_ids"]]

    catchup_mode = os.getenv("CATCHUP_MODE", "false").lower() == "true"
    if catchup_mode:
        # Hech narsa POSTLAMAYMIZ - faqat hammasini "ko'rilgan/band" deb belgilaymiz.
        for item in new_items:
            state["posted_ids"].append(item["id"])
        print(f"[Catchup] {len(new_items)} ta eski xabar postlamasdan 'ko'rilgan' deb belgilandi.")
        save_state(state)
        return

    primary_items = [i for i in new_items if i.get("priority", "primary") == "primary"]
    secondary_items = [i for i in new_items if i.get("priority") == "secondary"]

    print(f"[Info] Jami topildi: {len(all_items)}, yangi: {len(new_items)} "
          f"(primary: {len(primary_items)}, secondary: {len(secondary_items)})")

    # ---------- 1) PRIMARY manbalar ----------
    for item in primary_items:
        wait_left = config.POST_INTERVAL_SECONDS - (time.time() - state.get("last_post_at", 0))
        if wait_left > 0:
            time.sleep(wait_left)

        try:
            result = translate_and_format(item["text"], channel_username, forced_manba=item.get("forced_manba"))
        except Exception as e:
            print(f"[Xato - qayta urinilamiz] {item['id']}: {e}")
            continue

        if result is None:
            state["posted_ids"].append(item["id"])
            continue

        dup_player = _is_duplicate(result, state, config.DUPLICATE_PLAYER_WINDOW_SECONDS)
        if dup_player:
            print(f"[Info] '{dup_player}' haqida allaqachon post bor - dublikat o'tkazib yuborildi")
            state["posted_ids"].append(item["id"])
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
            print(f"[Xato - qayta urinilamiz] {item['id']}: {e}")
            continue

        if result is None:
            state["posted_ids"].append(item["id"])
            state["pending"].pop(item["id"], None)
            continue

        dup_player = _is_duplicate(result, state, config.SECONDARY_HOLD_SECONDS)
        if dup_player:
            print(f"[Info] '{dup_player}' haqida allaqachon post bor - o'tkazib yuborildi")
            state["posted_ids"].append(item["id"])
            state["pending"].pop(item["id"], None)
            continue

        if not _can_post_now(state):
            continue

        if _finalize_post(item, result, state, forced_manba="Fabrizio Romano"):
            state["pending"].pop(item["id"], None)
        time.sleep(3)

    save_state(state)


if __name__ == "__main__":
    run_once()
