"""
Barcha sozlamalar shu yerda. Maxfiy kalitlar (.env) orqali keladi,
manbalar ro'yxatini esa shu faylda to'g'ridan-to'g'ri tahrirlaysiz.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ---------- MAXFIY KALITLAR (.env faylidan) ----------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

_raw_api_id = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_ID = int(_raw_api_id) if _raw_api_id and _raw_api_id.isdigit() else None
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING")

# ---------- MANBALAR ----------
# RSS manbalar - o'chirilgan.
RSS_SOURCES = []

# Telegram public kanallar - hozircha FAQAT 2 ta asosiy manba.
TELEGRAM_SOURCES = [
    {"channel": "fabrizioromano_fans", "no_filter": True, "priority": "primary", "fetch_limit": 30, "forced_manba": "Fabrizio Romano"},
    {"channel": "Romano_tg", "no_filter": True, "priority": "primary", "fetch_limit": 30, "forced_manba": "Fabrizio Romano"},
]

# Postlar orasidagi minimal interval (soniyada)
POST_INTERVAL_SECONDS = 10

# Bir xil xabar dublikat bo'lmasligi uchun vaqt oynasi (soniyada)
DUPLICATE_WINDOW_SECONDS = 2 * 60 * 60

# Ikkinchi darajali manbalar postlashdan oldin shuncha kutadi (soniyada)
SECONDARY_HOLD_SECONDS = 2 * 60 * 60

# Filtr: shu so'zlardan kamida bittasi bo'lmasa, xabar o'tkazilmaydi.
KEYWORDS = [
    "transfer", "signs", "sign", "deal", "here we go", "medical",
    "loan", "fee", "contract", "£", "€", "$", "join", "move",
    "трансфер", "переход", "подпис", "сделк", "личны", "личных условия",
    "медосмотр", "аренд", "переговор", "согласие", "контракт", "клуб",
]

# Bloklash filtri: shu so'zlardan BIRORTASI xabarda uchrasa, u umuman
# ko'rib chiqilmaydi (Gemini'ga ham yuborilmaydi) - qimor/stavka reklamalari.
# no_filter=True bo'lgan manbalar uchun ham bu filtr HAR DOIM ishlaydi.
BLOCKED_KEYWORDS = [
    "1xbet", "1хбет", "mostbet", "мостбет", "melbet", "мелбет",
    "fonbet", "фонбет", "parimatch", "париматч", "betwinner", "бетвиннер",
    "bet365", "olimpbet", "олимпбет", "winline", "винлайн", "leon", "леон",
    "stavka", "stavki", "ставка", "ставки", "ставок", "коэффициент",
    "koeffitsient", "koeffitsent", "прогноз на матч", "прогноз матча",
    "прогнозы на футбол", "prognoz", "букмекер", "bukmeker", "казино",
    "kazino", "casino", "промокод", "promokod", "фрибет", "fribet",
    "azartli o'yin", "азартные игры",
]

# Gemini modeli - yuqori tezlik va katta kvotali model
GEMINI_MODEL = "gemini-3.5-flash-lite"

# Botning doimiy siklda (loop) tekshirish intervali (soniyada)
POLL_INTERVAL_SECONDS = 60



