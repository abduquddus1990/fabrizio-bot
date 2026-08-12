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
- Hech qanday izoh, preambula yozma - faqat JSON qaytar, boshqa hech narsa yo'q
- Agar matn futbol transferiga umuman aloqador bo'lmasa (masalan turmush qurish,
  match jadvali, reklama, umumiy yangilik), "relevant": false qaytar
- Agar matn qimor/bukmekerlik reklamasi bo'lsa (stavka, koeffitsient, prognoz,
  bukmeker kontorasi, kazino, promokod va shunga o'xshash - 1xbet, Mostbet, Melbet,
  Fonbet, Parimatch kabi xizmatlar tilga olinsa) - BU HAM "relevant": false, hech
  qachon transfer yangiligi sifatida qabul qilinmaydi

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

TELEGRAM_TEMPLATE = """*🚨 EXCLUSIVE TRANSFER*
_⚽️ {sarlavha}_

{tafsilot}

*Manba:* {manba}
*Status:* {status_badge}

📢 @{channel}"""


GEMINI_TIMEOUT_MS = 30_000  # bitta Gemini chaqiruvi shuncha vaqtdan ortiq osilib qolmasin
CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")


def _extract_json(text: str) -> dict:
    cleaned = re.sub(r"```json|```", "", text).strip()
    return json.loads(cleaned)


def _escape_markdown(text: str) -> str:
    for ch in ("_", "*", "`", "["):
        text = text.replace(ch, "\\" + ch)
    return text


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
            http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
        ),
    )
    return _extract_json(response.text)


def translate_and_format(raw_text: str, channel_username: str, forced_manba: str | None = None) -> dict | None:
    """
    forced_manba: berilsa, Gemini aniqlagan manba o'rniga shu qiymat ishlatiladi
    """
    data = _generate(raw_text)

    if not data.get("relevant", False):
        return None

    if _has_cyrillic(data):
        # Gemini rus/kirill matnini to'liq tarjima qilmadi - bir marta qattiqroq
        # ko'rsatma bilan qayta urinamiz.
        retry_data = _generate(
            raw_text,
            extra_instruction="DIQQAT: avvalgi javobingda kirill harflari qoldi. "
                               "Butun JSON FAQAT lotin alifbosidagi o'zbek tilida bo'lishi shart, "
                               "hech qanday kirill harfi ishlatma.",
        )
        if retry_data.get("relevant", False) and not _has_cyrillic(retry_data):
            data = retry_data
        elif _has_cyrillic(data):
            raise ValueError("Gemini kirill/rus tilidan to'liq tarjima qila olmadi (2 urinishdan keyin ham)")

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
