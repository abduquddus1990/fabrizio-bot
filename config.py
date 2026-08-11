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

TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
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

# Bir xil futbolchi haqida turli kanallardan bir xil yangilik kelsa,
# ikkinchisini "dublikat" deb hisoblab, postlamaslik uchun shuncha vaqt (soniyada)
DUPLICATE_PLAYER_WINDOW_SECONDS = 3 * 60 * 60

# Ikkinchi darajali manbalar postlashdan oldin shuncha kutadi (soniyada)
SECONDARY_HOLD_SECONDS = 2 * 60 * 60

# Filtr: shu so'zlardan kamida bittasi bo'lmasa, xabar o'tkazilmaydi.
KEYWORDS = [
    "transfer", "signs", "sign", "deal", "here we go", "medical",
    "loan", "fee", "contract", "£", "€", "$", "join", "move",
    "трансфер", "переход", "подпис", "сделк", "личны", "личных условия",
    "медосмотр", "аренд", "переговор", "согласие", "контракт", "клуб",
]

# Gemini modeli
GEMINI_MODEL = "gemini-3.1-flash-lite"

POLL_INTERVAL_SECONDS = 300
