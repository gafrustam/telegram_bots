import json
import logging
import re
from typing import Optional

from google import genai
from google.genai import types

from config import Config

logger = logging.getLogger(__name__)

_CLIENT = genai.Client(api_key=Config.GOOGLE_API_KEY)
_MODEL = "gemini-2.5-flash"

SCENARIO_EMOJIS = ["🐻", "📉", "📊", "📈", "🚀"]

# JSON schema to enforce correct types from Gemini
_SCENARIO_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "scenarios": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "label":       types.Schema(type=types.Type.STRING),
                    "probability": types.Schema(type=types.Type.INTEGER),
                    "price":       types.Schema(type=types.Type.NUMBER),
                    "rationale":   types.Schema(type=types.Type.STRING),
                },
                required=["label", "probability", "price", "rationale"],
            ),
        )
    },
    required=["scenarios"],
)


async def generate_scenarios(
    name: str, symbol: str, current_price: float, atl: Optional[float] = None
) -> list[dict]:
    """
    Generate 5 price scenarios for a token 3 years from now using Gemini.
    Returns list of dicts: emoji, label, probability (int), price (float), rationale (str).
    """
    atl_line = f"ATL (исторический минимум): ${atl:.8f}" if atl else ""
    prompt = (
        f"Ты криптоаналитик. Создай 5 ценовых сценариев для токена {name} ({symbol}) "
        f"на 3 года вперёд.\n\n"
        f"Текущая цена: ${current_price:.6f}\n"
        f"{atl_line}\n\n"
        f"Сценарии (в порядке от худшего к лучшему): медведь, пессимист, базовый, оптимист, суперцикл.\n"
        f"Названия сценариев должны быть на РУССКОМ языке.\n"
        f"Вероятности должны быть целыми числами (без знака %), их сумма = 100.\n"
        f"Цена — число с плавающей точкой в USD (без символов $ или USD).\n"
        f"Rationale — 1-2 предложения на русском.\n"
    )

    try:
        response = await _CLIENT.aio.models.generate_content(
            model=_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=4096,
                response_mime_type="application/json",
                response_schema=_SCENARIO_SCHEMA,
            ),
        )
        data = json.loads(response.text)
        scenarios_raw = data.get("scenarios", [])

        result = []
        for i, s in enumerate(scenarios_raw[:5]):
            emoji = SCENARIO_EMOJIS[i] if i < len(SCENARIO_EMOJIS) else "•"
            prob = s.get("probability", 20)
            price = s.get("price", 0)
            # Defensive: handle if API returned string despite schema
            if isinstance(prob, str):
                prob = int(re.sub(r"[^\d]", "", prob) or "20")
            if isinstance(price, str):
                price = float(re.sub(r"[^\d.]", "", price) or "0")
            result.append({
                "emoji": emoji,
                "label": s.get("label", ""),
                "probability": int(prob),
                "price": float(price),
                "rationale": s.get("rationale", ""),
            })
        return result

    except Exception:
        logger.exception("Error generating scenarios for %s", name)
        return []
