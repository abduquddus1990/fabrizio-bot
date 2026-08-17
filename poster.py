"""Telegram Bot API orqali o'z kanalimizga post yuborish (rasm bilan yoki rasmsiz)."""
import time
import requests
import config

CAPTION_LIMIT = 1024
TEXT_LIMIT = 4096


def _safe_send_request(url: str, data: dict, files: dict | None = None, is_json: bool = False) -> requests.Response | None:
    for attempt in range(3):
        try:
            if is_json:
                resp = requests.post(url, json=data, timeout=20)
            elif files:
                resp = requests.post(url, data=data, files=files, timeout=30)
            else:
                resp = requests.post(url, data=data, timeout=30)

            if resp.status_code == 429:
                retry_after = int(resp.json().get("parameters", {}).get("retry_after", 5))
                print(f"[Telegram 429] Rate limit. {retry_after} soniya kutilmoqda...")
                time.sleep(retry_after + 1)
                continue

            return resp
        except Exception as e:
            print(f"[Telegram so'rov xatosi - {attempt+1}/3] {e}")
            time.sleep(2)
    return None


def post_to_channel(text: str, image_url: str | None = None, image_bytes: bytes | None = None) -> bool:
    if not config.TELEGRAM_BOT_TOKEN or not config.TARGET_CHANNEL:
        print("[Xato] TELEGRAM_BOT_TOKEN yoki TARGET_CHANNEL sozlanmagan!")
        return False

    base_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"

    # Agar rasm bo'lsa va matn caption limitiga sig'sa
    if image_url or image_bytes:
        caption = text
        if len(caption) > CAPTION_LIMIT:
            # Agar caption juda uzun bo'lsa, avval rasmsiz to'liq matn jo'natish xavfsizroq
            caption = None

        if caption is not None:
            photo_data = {"chat_id": config.TARGET_CHANNEL, "caption": caption, "parse_mode": "HTML"}
            files = {"photo": ("photo.jpg", image_bytes)} if image_bytes else None
            if not image_bytes:
                photo_data["photo"] = image_url

            resp = _safe_send_request(f"{base_url}/sendPhoto", photo_data, files=files)
            if resp and resp.ok:
                return True

            print(f"[Telegram rasm yuborishda xatolik - matn sifatida qayta urinamiz] {resp.status_code if resp else 'No resp'}: {resp.text if resp else ''}")

    # Matn sifatida yuborish
    resp = _safe_send_request(
        f"{base_url}/sendMessage",
        data={
            "chat_id": config.TARGET_CHANNEL,
            "text": text[:TEXT_LIMIT],
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        is_json=True,
    )
    if resp and resp.ok:
        return True

    print(f"[Telegram post xatosi] {resp.status_code if resp else 'No resp'}: {resp.text if resp else ''}")
    return False

