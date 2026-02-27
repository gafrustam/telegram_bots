import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GOOGLE_AI_API_KEY: str = os.getenv("GOOGLE_AI_API_KEY", "")
AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai")

# ── Prize ladder (Russian TV show values) ────────────────────────────────────
PRIZE_LADDER: list[int] = [
    500,        # 1
    1_000,      # 2
    2_000,      # 3
    3_000,      # 4
    5_000,      # 5  🔒 safe haven
    10_000,     # 6
    15_000,     # 7
    25_000,     # 8
    50_000,     # 9
    100_000,    # 10 🔒 safe haven
    200_000,    # 11
    400_000,    # 12
    800_000,    # 13
    1_500_000,  # 14
    3_000_000,  # 15 🏆 jackpot
]

SAFE_HAVENS: dict[int, int] = {5: 5_000, 10: 100_000}

TOTAL_QUESTIONS = 15

# ── Difficulty descriptions for prompt ───────────────────────────────────────
DIFFICULTY: dict[tuple[int, int], str] = {
    (1, 5): (
        "очень лёгкие",
        "Базовые школьные знания, которые знает 9 из 10 взрослых. "
        "Примеры: самые известные столицы, элементарная математика, "
        "всемирно известные исторические личности и события.",
    ),
    (6, 10): (
        "средние",
        "Широкий кругозор образованного человека. "
        "История, наука, культура, спорт — факты, которые знают любители интеллектуальных игр.",
    ),
    (11, 15): (
        "сложные",
        "Специализированные знания. Точные даты, узкие исторические факты, "
        "детальная география, литература, сложные науки — вопросы, которые затрудняют даже эрудитов.",
    ),
}


def get_difficulty(level: int) -> tuple[str, str]:
    for (lo, hi), desc in DIFFICULTY.items():
        if lo <= level <= hi:
            return desc
    return ("средние", "общие знания")


# ── Money helpers ─────────────────────────────────────────────────────────────
def fmt(amount: int) -> str:
    """Format integer as money string, e.g. 1500000 → '1 500 000 ₽'."""
    return f"{amount:,}".replace(",", "\u202f") + "\u00a0₽"


def prize(level: int) -> int:
    """Prize amount for completing level (1-indexed)."""
    return PRIZE_LADDER[level - 1]


def safe_haven_amount(level: int) -> int:
    """Guaranteed minimum if player answers wrong at given level."""
    if level <= 5:
        return 0
    elif level <= 10:
        return SAFE_HAVENS[5]
    return SAFE_HAVENS[10]


def walkaway_amount(level: int) -> int:
    """Amount player gets by walking away before answering level."""
    return PRIZE_LADDER[level - 2] if level > 1 else 0
