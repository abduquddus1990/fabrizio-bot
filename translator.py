"""
Xom transfer yangilikni Gemini orqali o'zbek tiliga tarjima qilib,
Telegram post formatiga o'giradi.
"""
import json
import re
from google import genai
from google.genai import types
import config

_client = genai.Client(api_key=config.GEMINI_API_KEY)

SYSTEM_PROMPT = """Sen professional futbol jurnalistisan va tarjimonsan. Fabrizio Romano
uslubida real transfer yangiliklarini ingliz yoki boshqa tildan o'zbek
tiliga (lotin alifbosida) professional darajada tarjima qilasan.

QOIDALAR:
- Futbolchi ismlari, klub nomlari, summalar, sanalar - o'zgarishsiz qoldiriladi
- Iqtiboslar so'zma-so'z tarjima qilinadi, mazmuni buzilmaydi
- Hech qanday izoh, preambula yozma - faqat JSON qaytar, boshqa hech narsa yo'q
- Agar matn futbol transferiga umuman aloqador bo'lmasa, "relevant": false qaytar

OUTPUT: faqat quyidagi JSON formatida javob ber (```json belgilarsiz, faqat xom JSON):
{
  "relevant": true yoki false,
  "futbolchilar": ["asosiy futbolchi(lar)ning TO'LIQ ismi va familiyasi, ingliz tilidagi original yozilishida (masalan 'Kylian Mbappe'). Agar bir nechta futbolchi tilga olingan bo'lsa, HAMMASINI shu ro'yxatga qo'sh, faqat bittasini emas"],
  "sarlavha": "qisqa jonli sarlavha",
  "tafsilot": "1-2 jumlada asosiy ma'lumot, summa va muddatlar bilan",
  "holat": "Muzokaralar / Shaxsiy shartlar / Tibbiy ko'rik / Rasman tasdiqlandi",
  "status_badge": "Here We Go! / Kelishuv hal qilindi / Muzokaralar davom etmoqda",
  "manba": "xabar qaysi manbadan kelgani (agar bilinmasa 'Sport manbalari')"
}
"""

TELEGRAM_TEMPLATE = """🚨 EXCLUSIVE TRANSFER
⚽️ {sarlavha}

{tafsilot}

Manba: {manba}
Status: {status_badge}

📢 @{channel}"""


def _extract_json(text: str) -> dict:
    cleaned = re.sub(r"```json|```", "", text).strip()
    return json.loads(cleaned)


def _escape_markdown(text: str) -> str:
    for ch in ("_", "*", "`", "["):
        text = text.replace(ch, "\\" + ch)
    return text


def translate_and_format(raw_text: str, channel_username: str, forced_manba: str | None = None) -> dict | None:
    """
    forced_manba: berilsa, Gemini aniqlagan manba o'rniga shu qiymat ishlatiladi
    """
    response = _client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=raw_text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        ),
    )
    data = _extract_json(response.text)

    if not data.get("relevant", False):
        return None

    manba_value = forced_manba if forced_manba else data["manba"]

    post_text = TELEGRAM_TEMPLATE.format(
        sarlavha=_escape_markdown(data["sarlavha"]),
        tafsilot=_escape_markdown(data["tafsilot"]),
        manba=_escape_markdown(manba_value),
        status_badge=_escape_markdown(data["status_badge"]),
        channel=channel_username,
    )

    return {
        "telegram_post": post_text,
        "sarlavha": data["sarlavha"],
        "futbolchilar": data.get("futbolchilar") or [],
    }
