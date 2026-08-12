"""
Public Telegram kanallardan oxirgi xabarlarni o'qiydi.
DIQQAT: bu bot emas - sizning shaxsiy Telegram akkountingiz orqali (Telethon)
ochiq (public) kanallardagi xabarlarni o'qiydi.
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import config


def fetch_telegram_items() -> list[dict]:
    items = []

    if not config.TELEGRAM_SESSION_STRING:
        print("[Telethon] SESSION_STRING yo'q - Telegram manbalar o'tkazib yuborildi. "
              "generate_session.py ni ishga tushiring.")
        return items

    with TelegramClient(
        StringSession(config.TELEGRAM_SESSION_STRING),
        config.TELEGRAM_API_ID,
        config.TELEGRAM_API_HASH,
    ) as client:
        for source in config.TELEGRAM_SOURCES:
            channel = source["channel"]
            no_filter = source.get("no_filter", False)
            keywords = source.get("keywords") or config.KEYWORDS
            priority = source.get("priority", "primary")
            fetch_limit = source.get("fetch_limit", 10)

            try:
                messages = client.get_messages(channel, limit=fetch_limit)
            except Exception as e:
                print(f"[Telethon xatosi] {channel}: {e}")
                continue

            for msg in messages:
                if not msg.text:
                    continue

                text_lower = msg.text.lower()
                if any(kw.lower() in text_lower for kw in config.BLOCKED_KEYWORDS):
                    continue
                if not no_filter and not any(kw.lower() in text_lower for kw in keywords):
                    continue

                image_bytes = None
                if msg.photo:
                    try:
                        image_bytes = client.download_media(msg, file=bytes)
                    except Exception as e:
                        print(f"[Telethon rasm yuklash xatosi] {channel}:{msg.id}: {e}")

                items.append({
                    "id": f"tg:{channel}:{msg.id}",
                    "text": msg.text,
                    "source": f"@{channel}",
                    "image_bytes": image_bytes,
                    "signature": source.get("signature"),
                    "priority": priority,
                    "forced_manba": source.get("forced_manba"),
                })
    return items
