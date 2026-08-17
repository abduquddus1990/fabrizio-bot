"""
Botning holatini saqlaydi: postlangan xabarlar, postlangan futbolchilar
(va qachon), ikkinchi darajali manbalardan "kutayotgan" postlar, va oxirgi
post vaqti.
"""
import json
import os

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_state.json")
MAX_POSTED_IDS = 500
MAX_POSTED_ITEMS = 300


def load_state() -> dict:
    default_state = {
        "posted_ids": [],
        "posted_titles": {},
        "posted_players": {},
        "pending": {},
        "last_post_at": 0,
    }
    if not os.path.exists(STATE_FILE):
        return default_state
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("posted_ids", [])
            data.setdefault("posted_titles", {})
            data.setdefault("posted_players", {})
            data.setdefault("pending", {})
            data.setdefault("last_post_at", 0)
            return data
    except Exception as e:
        print(f"[Storage] bot_state.json o'qishda xatolik ({e}), standart holat tiklanmoqda...")
        return default_state


def save_state(state: dict):
    state["posted_ids"] = state["posted_ids"][-MAX_POSTED_IDS:]
    if len(state.get("posted_titles", {})) > MAX_POSTED_ITEMS:
        sorted_items = sorted(state["posted_titles"].items(), key=lambda x: x[1])
        state["posted_titles"] = dict(sorted_items[-MAX_POSTED_ITEMS:])
    if len(state.get("posted_players", {})) > MAX_POSTED_ITEMS:
        sorted_items = sorted(state["posted_players"].items(), key=lambda x: x[1])
        state["posted_players"] = dict(sorted_items[-MAX_POSTED_ITEMS:])

    tmp_file = STATE_FILE + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, STATE_FILE)
    except Exception as e:
        print(f"[Storage xatosi] bot_state.json saqlanmadi: {e}")

