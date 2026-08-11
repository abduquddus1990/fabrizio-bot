"""Telegram Bot API orqali o'z kanalimizga post yuborish (rasm bilan yoki rasmsiz)."""
import requests
import config

CAPTION_LIMIT = 1024
TEXT_LIMIT = 4096


def post_to_channel(text: str, image_url: str | None = None, image_bytes: bytes | None = None) -> bool:
    base_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"

    if image_url or image_bytes:
        caption = text if len(text) <= CAPTION_LIMIT else text[:CAPTION_LIMIT - 3] + "..."
        try:
            if image_bytes:
                resp = requests.post(
                    f"{base_url}/sendPhoto",
                    data={"chat_id": config.TARGET_CHANNEL, "caption": caption, "parse_mode": "Markdown"},
                    files={"photo": ("photo.jpg", image_bytes)},
                    timeout=30,
                )
            else:
                resp = requests.post(
                    f"{base_url}/sendPhoto",
                    data={"chat_id": config.TARGET_CHANNEL, "caption": caption, "photo": image_url, "parse_mode": "Markdown"},
                    timeout=30,
                )

            if resp.ok:
                return True

            print(f"[Telegram rasm xatosi - matn sifatida qayta urinamiz] {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[Telegram rasm xatosi - matn sifatida qayta urinamiz] {e}")

    try:
        resp = requests.post(
            f"{base_url}/sendMessage",
            json={
                "chat_id": config.TARGET_CHANNEL,
                "text": text[:TEXT_LIMIT],
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        if not resp.ok:
            print(f"[Telegram post xatosi] {resp.status_code}: {resp.text}")
            return False
        return True
    except Exception as e:
        print(f"[Telegram post xatosi] {e}")
        return False
