"""
Botning holatini saqlaydi: postlangan xabarlar, postlangan futbolchilar
(va qachon), ikkinchi darajali manbalardan "kutayotgan" postlar, va oxirgi
post vaqti.
"""
import json
import os

STATE_FILE = "bot_state.json"
MAX_POSTED_IDS = 500
MAX_POSTED_PLAYERS = 200


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {
            "posted_ids": [],
            "posted_players": {},
            "pending": {},
            "last_post_at": 0,
        }
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        data.setdefault("posted_ids", [])
        data.setdefault("posted_players", {})
        data.setdefault("pending", {})
        data.setdefault("last_post_at", 0)
        return data


def save_state(state: dict):
    state["posted_ids"] = state["posted_ids"][-MAX_POSTED_IDS:]
    if len(state["posted_players"]) > MAX_POSTED_PLAYERS:
        sorted_items = sorted(state["posted_players"].items(), key=lambda x: x[1])
        state["posted_players"] = dict(sorted_items[-MAX_POSTED_PLAYERS:])
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
