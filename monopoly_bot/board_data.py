"""Kazan Monopoly board definition."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Property:
    id: int
    name: str
    type: str           # "property" | "railroad" | "utility" | "tax" | "corner" | "chance" | "chest"
    color: Optional[str] = None   # color group for properties
    price: int = 0
    house_cost: int = 0
    rents: list = field(default_factory=list)   # [base, 1h, 2h, 3h, 4h, hotel]
    mortgage_value: int = 0
    district: Optional[str] = None


# Board spaces — 40 total, starting from GO (index 0), clockwise
BOARD: list[Property] = [
    # 0
    Property(0,  "СТАРТ",                    "corner"),
    # 1-9 (side 1)
    Property(1,  "ул. Горьковское шоссе",    "property", "brown",  60,  50, [2, 10, 30, 90, 160, 250], 30,  "Кировский р-н"),
    Property(2,  "Городской фонд",           "chest"),
    Property(3,  "ул. Краснококшайская",     "property", "brown",  60,  50, [4, 20, 60, 180, 320, 450], 30, "Кировский р-н"),
    Property(4,  "Подоходный налог",         "tax",    price=200),
    Property(5,  "ст. м. Дубравная",         "railroad", price=200, rents=[25, 50, 100, 200]),
    Property(6,  "ул. Копылова",             "property", "lblue", 100,  50, [6, 30, 90, 270, 400, 550],  50, "Авиастроительный р-н"),
    Property(7,  "Шанс",                     "chance"),
    Property(8,  "ул. Дементьева",           "property", "lblue", 100,  50, [6, 30, 90, 270, 400, 550],  50, "Авиастроительный р-н"),
    Property(9,  "ул. Гагарина",             "property", "lblue", 120,  50, [8, 40, 100, 300, 450, 600], 60, "Авиастроительный р-н"),
    # 10
    Property(10, "Тюрьма / Просто визит",    "corner"),
    # 11-19
    Property(11, "ул. Декабристов",          "property", "pink",  140,  100, [10, 50, 150, 450, 625, 750],  70, "Московский р-н"),
    Property(12, "Таттелеком",               "utility",  price=150),
    Property(13, "ул. Калинина",             "property", "pink",  140,  100, [10, 50, 150, 450, 625, 750],  70, "Московский р-н"),
    Property(14, "пр. Ибрагимова",           "property", "pink",  160,  100, [12, 60, 180, 500, 700, 900],  80, "Московский р-н"),
    Property(15, "ст. м. Горки",             "railroad", price=200, rents=[25, 50, 100, 200]),
    Property(16, "ул. Чистопольская",        "property", "orange",180,  100, [14, 70, 200, 550, 750, 950],  90, "Советский р-н"),
    Property(17, "Городской фонд",           "chest"),
    Property(18, "пр. Ямашева",              "property", "orange",180,  100, [14, 70, 200, 550, 750, 950],  90, "Советский р-н"),
    Property(19, "ул. Сибгата Хакима",       "property", "orange",200,  100, [16, 80, 220, 600, 800, 1000], 100, "Советский р-н"),
    # 20
    Property(20, "Бесплатная стоянка",       "corner"),
    # 21-29
    Property(21, "ул. Космонавтов",          "property", "red",   220,  150, [18, 90, 250, 700, 875, 1050], 110, "Ново-Савиновский р-н"),
    Property(22, "Шанс",                     "chance"),
    Property(23, "пр. Победы",               "property", "red",   220,  150, [18, 90, 250, 700, 875, 1050], 110, "Ново-Савиновский р-н"),
    Property(24, "ул. Четаева",              "property", "red",   240,  150, [20, 100, 300, 750, 925, 1100], 120, "Ново-Савиновский р-н"),
    Property(25, "ст. м. Проспект Победы",   "railroad", price=200, rents=[25, 50, 100, 200]),
    Property(26, "ул. Пушкина",              "property", "yellow",260,  150, [22, 110, 330, 800, 975, 1150], 130, "Вахитовский р-н"),
    Property(27, "ул. Муштари",              "property", "yellow",260,  150, [22, 110, 330, 800, 975, 1150], 130, "Вахитовский р-н"),
    Property(28, "Татэнергосбыт",            "utility",  price=150),
    Property(29, "ул. Университетская",      "property", "yellow",280,  150, [24, 120, 360, 850, 1025, 1200], 140, "Вахитовский р-н"),
    # 30
    Property(30, "Иди в тюрьму",             "corner"),
    # 31-39
    Property(31, "ул. Лобачевского",         "property", "green", 300,  200, [26, 130, 390, 900, 1100, 1275], 150, "Вахитовский р-н"),
    Property(32, "ул. Кремлёвская",          "property", "green", 300,  200, [26, 130, 390, 900, 1100, 1275], 150, "Вахитовский р-н"),
    Property(33, "Городской фонд",           "chest"),
    Property(34, "ул. Баумана",              "property", "green", 320,  200, [28, 150, 450, 1000, 1200, 1400], 160, "Вахитовский р-н"),
    Property(35, "ст. м. Кремлёвская",       "railroad", price=200, rents=[25, 50, 100, 200]),
    Property(36, "Шанс",                     "chance"),
    Property(37, "ул. Шейнкмана",            "property", "dblue", 350,  200, [35, 175, 500, 1100, 1300, 1500], 175, "Казанский Кремль"),
    Property(38, "Налог на роскошь",         "tax",      price=100),
    Property(39, "пл. Тысячелетия",          "property", "dblue", 400,  200, [50, 200, 600, 1400, 1700, 2000], 200, "Казанский Кремль"),
]

# Color group info
COLOR_GROUPS = {
    "brown":  {"name": "Кировский р-н",        "color": "#8B4513", "count": 2},
    "lblue":  {"name": "Авиастроительный р-н",  "color": "#87CEEB", "count": 3},
    "pink":   {"name": "Московский р-н",        "color": "#FF69B4", "count": 3},
    "orange": {"name": "Советский р-н",         "color": "#FFA500", "count": 3},
    "red":    {"name": "Ново-Савиновский р-н",  "color": "#FF0000", "count": 3},
    "yellow": {"name": "Вахитовский р-н (внеш)","color": "#FFD700", "count": 3},
    "green":  {"name": "Вахитовский р-н (центр)","color": "#008000", "count": 3},
    "dblue":  {"name": "Казанский Кремль",      "color": "#00008B", "count": 2},
}

# Indexes by type (for quick lookup)
RAILROAD_IDS = [s.id for s in BOARD if s.type == "railroad"]
UTILITY_IDS  = [s.id for s in BOARD if s.type == "utility"]
PROPERTY_IDS = [s.id for s in BOARD if s.type == "property"]


def board_dict():
    """Return board as a list of dicts for JSON serialization."""
    result = []
    for s in BOARD:
        d = {
            "id": s.id,
            "name": s.name,
            "type": s.type,
        }
        if s.color:
            d["color"] = s.color
        if s.price:
            d["price"] = s.price
        if s.house_cost:
            d["house_cost"] = s.house_cost
        if s.rents:
            d["rents"] = s.rents
        if s.mortgage_value:
            d["mortgage_value"] = s.mortgage_value
        if s.district:
            d["district"] = s.district
        result.append(d)
    return result
