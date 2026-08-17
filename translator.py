"""
Xom transfer yangilikni Gemini orqali o'zbek tiliga tarjima qilib,
Telegram post formatiga o'giradi.
"""
import json
import re
import html
from google import genai
from google.genai import types
import config

_client = genai.Client(api_key=config.GEMINI_API_KEY)

SYSTEM_PROMPT = """Sen professional futbol jurnalistisan va tarjimonsan. Fabrizio Romano
uslubida real transfer yangiliklarini (manba matni ko'pincha RUS tilida keladi,
ba'zan ingliz yoki boshqa tilda) o'zbek tiliga (FAQAT lotin alifbosida) professional
darajada tarjima qilasan.

QOIDALAR:
- CHIQISH MATNI (barcha JSON maydonlari) 100% o'zbek tilida, FAQAT lotin alifbosida
  bo'lishi SHART. Kirill harflari (masalan: а, б, в, г, д ...) chiqishda BITTA HAM
  bo'lmasligi kerak - hatto bitta so'z ham rus tilida qoldirilmaydi.
- Futbolchi ismlari va klub nomlari xalqaro standart LOTIN yozuvida beriladi
  (masalan manbada "Погба" kelsa - "Pogba" deb yoz, "Роналду" - "Ronaldo",
  "Криштиану Роналду" - "Cristiano Ronaldo", "Монако" - "Monako", "Арсенал" -
  "Arsenal"). Ismlarni kirillchada yoki rus tilida transliteratsiya qilib qoldirma.
- Summalar va sanalar - o'zgarishsiz qoldiriladi (raqamlar allaqachon universal)
- Iqtiboslar mazmuni buzilmasdan o'zbek tiliga tarjima qilinadi (rus tilida qoldirilmaydi)
- Faqat toza JSON formatida javob ber.
- Agar matn futbol transferiga umuman aloqador bo'lmasa (masalan turmush qurish,
  match jadvali, reklama, umumiy yangilik), "relevant": false qaytar
- Agar matn qimor/bukmekerlik reklamasi bo'lsa (stavka, koeffitsient, prognoz,
  bukmeker kontorasi, kazino, promokod va shunga o'xshash - 1xbet, Mostbet, Melbet,
  Fonbet, Parimatch kabi xizmatlar tilga olinsa) - BU HAM "relevant": false, hech
  qachon transfer yangiligi sifatida qabul qilinmaydi

OUTPUT JSON formati:
{
  "relevant": true yoki false,
  "futbolchilar": ["futbolchilarning to'liq ismi (masalan 'Kylian Mbappe')"],
  "sarlavha": "qisqa jonli sarlavha",
  "tafsilot": "1-2 jumlada asosiy ma'lumot, summa va muddatlar bilan",
  "holat": "Muzokaralar / Shaxsiy shartlar / Tibbiy ko'rik / Rasman tasdiqlandi",
  "status_badge": "Here We Go! / Kelishuv hal qilindi / Muzokaralar davom etmoqda",
  "manba": "xabar qaysi manbadan kelgani (masalan 'Fabrizio Romano' yoki 'Sport manbalari')"
}
"""

TELEGRAM_TEMPLATE_HTML = """<b>🚨 EXCLUSIVE TRANSFER</b>
<i>⚽️ {sarlavha}</i>

{tafsilot}

<b>Manba:</b> {manba}
<b>Status:</b> {status_badge}

📢 @{channel}"""


GEMINI_TIMEOUT_MS = 30_000
CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")


def _extract_json(text: str) -> dict:
    if not text:
        return {}
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(cleaned, strict=False)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0), strict=False)
            except Exception:
                pass
        raise



def _has_cyrillic(data: dict) -> bool:
    return any(CYRILLIC_RE.search(str(data.get(field, ""))) for field in
               ("sarlavha", "tafsilot", "holat", "status_badge", "manba"))


def _generate(raw_text: str, extra_instruction: str | None = None) -> dict:
    contents = raw_text if not extra_instruction else f"{raw_text}\n\n[{extra_instruction}]"
    response = _client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
        ),
    )
    return _extract_json(response.text)


def translate_and_format(raw_text: str, channel_username: str, forced_manba: str | None = None) -> dict | None:
    """
    forced_manba: berilsa, Gemini aniqlagan manba o'rniga shu qiymat ishlatiladi
    """
    try:
        data = _generate(raw_text)
    except Exception as e:
        print(f"[Gemini tarjima xatosi] {e}")
        return None

    if not data or not data.get("relevant", False):
        return None

    if _has_cyrillic(data):
        try:
            retry_data = _generate(
                raw_text,
                extra_instruction="DIQQAT: avvalgi javobingda kirill harflari qoldi. "
                                  "Butun JSON FAQAT lotin alifbosidagi o'zbek tilida bo'lishi shart, "
                                  "hech qanday kirill harfi ishlatma.",
            )
            if retry_data.get("relevant", False) and not _has_cyrillic(retry_data):
                data = retry_data
            else:
                print("[Ogohlantirish] Gemini 2-urinishda ham kirill harflarini qoldirdi. Xabar o'tkazib yuboriladi.")
                return None
        except Exception as e:
            print(f"[Gemini qayta urinish xatosi] {e}")
            return None

    sarlavha = data.get("sarlavha") or "Transfer yangiligi"
    tafsilot = data.get("tafsilot") or ""
    status_badge = data.get("status_badge") or "Muzokaralar davom etmoqda"
    manba_value = forced_manba if forced_manba else (data.get("manba") or "Sport manbalari")

    post_text = TELEGRAM_TEMPLATE_HTML.format(
        sarlavha=html.escape(sarlavha),
        tafsilot=html.escape(tafsilot),
        manba=html.escape(manba_value),
        status_badge=html.escape(status_badge),
        channel=channel_username,
    )

    return {
        "telegram_post": post_text,
        "sarlavha": sarlavha,
        "futbolchilar": data.get("futbolchilar") or [],
    }

