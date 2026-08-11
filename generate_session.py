"""
Buni FAQAT BIR MARTA, o'z kompyuteringizda ishga tushirasiz.
Telefon raqamingiz va SMS kod bilan tasdiqlaysiz, natijada chiqadigan
"session string"ni .env fayliga (TELEGRAM_SESSION_STRING=...) qo'yasiz.

Ishga tushirish: python generate_session.py
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = input("api_id (my.telegram.org dan): ")
API_HASH = input("api_hash (my.telegram.org dan): ")

with TelegramClient(StringSession(), int(API_ID), API_HASH) as client:
    print("\n=== SESSION STRING (buni .env fayliga TELEGRAM_SESSION_STRING= qatoriga joylang) ===\n")
    print(client.session.save())
    print("\n=== DIQQAT: bu stringni hech kimga bermang ===")
