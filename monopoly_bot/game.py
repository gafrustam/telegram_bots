"""Core Monopoly game logic."""

import random
import uuid
from dataclasses import dataclass, field
from typing import Optional

from board_data import BOARD, RAILROAD_IDS, UTILITY_IDS, COLOR_GROUPS, PROPERTY_IDS
from card_data import make_decks


STARTING_MONEY = 1500
GO_BONUS = 200
JAIL_POSITION = 10
JAIL_BAIL = 50
MAX_JAIL_TURNS = 3


@dataclass
class OwnedProperty:
    position: int
    houses: int = 0        # 0-4 = houses, 5 = hotel
    mortgaged: bool = False


@dataclass
class Player:
    id: str
    name: str
    is_ai: bool = False
    money: int = STARTING_MONEY
    position: int = 0
    in_jail: bool = False
    jail_turns: int = 0
    jail_free_cards: int = 0
    properties: dict = field(default_factory=dict)   # pos -> OwnedProperty
    bankrupt: bool = False
    doubles_streak: int = 0
    color: str = "#4ade80"


@dataclass
class GameState:
    game_id: str
    status: str = "lobby"      # lobby | playing | finished
    players: list = field(default_factory=list)
    current_player_idx: int = 0
    dice: tuple = (0, 0)
    dice_rolled: bool = False
    phase: str = "roll"        # roll | buy_decision | card | end_turn
    pending: dict = field(default_factory=dict)   # extra info for current phase
    max_humans: int = 2
    max_ai: int = 0
    owner_id: str = ""
    winner: Optional[str] = None
    chance_deck: list = field(default_factory=list)
    chest_deck: list = field(default_factory=list)
    log: list = field(default_factory=list)        # recent event messages

    def __post_init__(self):
        c, ch = make_decks()
        self.chance_deck = c
        self.chest_deck = ch


# ── Global lobby ──────────────────────────────────────────────────────────────
_games: dict[str, GameState] = {}


def list_open_games() -> list[dict]:
    return [
        {
            "game_id": g.game_id,
            "owner": g.players[0].name if g.players else "?",
            "humans": len([p for p in g.players if not p.is_ai]),
            "max_humans": g.max_humans,
            "ai": g.max_ai,
        }
        for g in _games.values()
        if g.status == "lobby"
        and len([p for p in g.players if not p.is_ai]) < g.max_humans
    ]


def create_game(owner_id: str, owner_name: str, max_humans: int, max_ai: int) -> GameState:
    gid = str(uuid.uuid4())[:8]
    colors = ["#4ade80", "#f87171", "#60a5fa", "#fbbf24", "#e879f9", "#34d399"]
    owner = Player(id=owner_id, name=owner_name, color=colors[0])
    g = GameState(
        game_id=gid,
        max_humans=max_humans,
        max_ai=max_ai,
        owner_id=owner_id,
    )
    g.players.append(owner)
    # Add AI players immediately
    for i in range(max_ai):
        ai = Player(
            id=f"ai_{gid}_{i}",
            name=f"ИИ {i+1}",
            is_ai=True,
            color=colors[len(g.players) % len(colors)],
        )
        g.players.append(ai)
    _games[gid] = g
    if _all_humans_joined(g):
        _start_game(g)
    return g


def join_game(game_id: str, player_id: str, player_name: str) -> Optional[GameState]:
    g = _games.get(game_id)
    if not g or g.status != "lobby":
        return None
    human_count = len([p for p in g.players if not p.is_ai])
    if human_count >= g.max_humans:
        return None
    colors = ["#4ade80", "#f87171", "#60a5fa", "#fbbf24", "#e879f9", "#34d399"]
    p = Player(id=player_id, name=player_name, color=colors[len(g.players) % len(colors)])
    g.players.append(p)
    if _all_humans_joined(g):
        _start_game(g)
    return g


def _all_humans_joined(g: GameState) -> bool:
    return len([p for p in g.players if not p.is_ai]) >= g.max_humans


def _start_game(g: GameState):
    random.shuffle(g.players)
    g.status = "playing"
    g.phase = "roll"
    g.log = ["Игра началась! Ходит: " + g.players[0].name]


def get_game(game_id: str) -> Optional[GameState]:
    return _games.get(game_id)


def remove_game(game_id: str):
    _games.pop(game_id, None)


# ── Game actions ──────────────────────────────────────────────────────────────

def current_player(g: GameState) -> Player:
    return g.players[g.current_player_idx]


def _log(g: GameState, msg: str):
    g.log.append(msg)
    if len(g.log) > 30:
        g.log = g.log[-30:]


def roll_dice(g: GameState) -> dict:
    """Roll dice for current player. Returns result dict."""
    p = current_player(g)
    if g.dice_rolled:
        return {"error": "Кубики уже брошены"}
    if g.phase != "roll":
        return {"error": "Сейчас не фаза броска"}

    d1 = random.randint(1, 6)
    d2 = random.randint(1, 6)
    g.dice = (d1, d2)
    g.dice_rolled = True
    is_double = d1 == d2

    if p.in_jail:
        return _handle_jail_roll(g, p, d1, d2, is_double)

    if is_double:
        p.doubles_streak += 1
        if p.doubles_streak >= 3:
            p.doubles_streak = 0
            _send_to_jail(g, p)
            _log(g, f"{p.name} бросил дубль три раза подряд — тюрьма!")
            g.phase = "end_turn"
            return _state_snapshot(g)
    else:
        p.doubles_streak = 0

    _move_player(g, p, d1 + d2)
    result = _land_on(g, p)
    if is_double and g.phase == "end_turn":
        # doubles but landed on go-to-jail already handled
        pass
    elif is_double:
        # Can roll again after handling current space
        g.dice_rolled = False
        g.phase = "roll"
    return result


def _handle_jail_roll(g: GameState, p: Player, d1: int, d2: int, is_double: bool) -> dict:
    if is_double:
        p.in_jail = False
        p.jail_turns = 0
        p.doubles_streak = 0
        _log(g, f"{p.name} вышел из тюрьмы двойником!")
        _move_player(g, p, d1 + d2)
        return _land_on(g, p)
    else:
        p.jail_turns += 1
        if p.jail_turns >= MAX_JAIL_TURNS:
            p.in_jail = False
            p.jail_turns = 0
            _pay(g, p, JAIL_BAIL, None)
            _log(g, f"{p.name} принудительно вышел из тюрьмы, заплатив {JAIL_BAIL}₽.")
            _move_player(g, p, d1 + d2)
            return _land_on(g, p)
        else:
            _log(g, f"{p.name} остаётся в тюрьме (ход {p.jail_turns}/{MAX_JAIL_TURNS}).")
            g.phase = "end_turn"
            return _state_snapshot(g)


def pay_jail_bail(g: GameState) -> dict:
    p = current_player(g)
    if not p.in_jail:
        return {"error": "Вы не в тюрьме"}
    if p.money < JAIL_BAIL:
        return {"error": "Недостаточно денег"}
    _pay(g, p, JAIL_BAIL, None)
    p.in_jail = False
    p.jail_turns = 0
    _log(g, f"{p.name} заплатил {JAIL_BAIL}₽ и вышел из тюрьмы.")
    g.phase = "roll"
    g.dice_rolled = False
    return _state_snapshot(g)


def use_jail_free_card(g: GameState) -> dict:
    p = current_player(g)
    if not p.in_jail or p.jail_free_cards < 1:
        return {"error": "Нет карты освобождения"}
    p.jail_free_cards -= 1
    p.in_jail = False
    p.jail_turns = 0
    _log(g, f"{p.name} использовал карту освобождения из тюрьмы.")
    g.phase = "roll"
    g.dice_rolled = False
    return _state_snapshot(g)


def _move_player(g: GameState, p: Player, steps: int):
    old_pos = p.position
    p.position = (p.position + steps) % 40
    if p.position < old_pos or (old_pos == 0 and steps > 0 and p.position != 0):
        # Passed GO
        if not p.in_jail:
            p.money += GO_BONUS
            _log(g, f"{p.name} прошёл СТАРТ, получил {GO_BONUS}₽.")


def _land_on(g: GameState, p: Player) -> dict:
    space = BOARD[p.position]
    _log(g, f"{p.name} остановился на «{space.name}».")

    if space.type == "corner":
        if p.position == 30:  # Go to Jail
            _send_to_jail(g, p)
        g.phase = "end_turn"

    elif space.type == "tax":
        amount = space.price
        _pay(g, p, amount, None)
        _log(g, f"{p.name} заплатил налог {amount}₽.")
        g.phase = "end_turn"

    elif space.type == "chance":
        return _draw_card(g, p, "chance")

    elif space.type == "chest":
        return _draw_card(g, p, "chest")

    elif space.type in ("property", "railroad", "utility"):
        owner = _find_owner(g, p.position)
        if owner is None:
            # Unowned — offer to buy
            g.phase = "buy_decision"
            g.pending = {"position": p.position, "price": space.price}
        elif owner.id == p.id:
            _log(g, f"{p.name} — это ваша собственность.")
            g.phase = "end_turn"
        else:
            rent = _calc_rent(g, p.position, owner, g.dice)
            _pay(g, p, rent, owner)
            _log(g, f"{p.name} заплатил аренду {rent}₽ игроку {owner.name}.")
            g.phase = "end_turn"

    return _state_snapshot(g)


def _send_to_jail(g: GameState, p: Player):
    p.position = JAIL_POSITION
    p.in_jail = True
    p.jail_turns = 0
    p.doubles_streak = 0
    _log(g, f"{p.name} отправлен в тюрьму!")


def _find_owner(g: GameState, position: int) -> Optional[Player]:
    for p in g.players:
        if position in p.properties:
            return p
    return None


def _calc_rent(g: GameState, position: int, owner: Player, dice: tuple) -> int:
    space = BOARD[position]
    prop = owner.properties[position]
    if prop.mortgaged:
        return 0

    if space.type == "railroad":
        rr_count = sum(1 for pos in RAILROAD_IDS if pos in owner.properties and not owner.properties[pos].mortgaged)
        return space.rents[rr_count - 1]

    if space.type == "utility":
        ut_count = sum(1 for pos in UTILITY_IDS if pos in owner.properties and not owner.properties[pos].mortgaged)
        multiplier = 4 if ut_count == 1 else 10
        return multiplier * (dice[0] + dice[1])

    # Regular property
    houses = prop.houses
    has_monopoly = _has_monopoly(owner, space.color)
    if houses == 0:
        rent = space.rents[0] * (2 if has_monopoly else 1)
    else:
        rent = space.rents[houses]
    return rent


def _has_monopoly(p: Player, color: str) -> bool:
    if not color:
        return False
    total = COLOR_GROUPS[color]["count"]
    owned = sum(1 for pos in PROPERTY_IDS if BOARD[pos].color == color and pos in p.properties)
    return owned >= total


def _pay(g: GameState, payer: Player, amount: int, receiver: Optional[Player]):
    amount = min(amount, payer.money)
    payer.money -= amount
    if receiver:
        receiver.money += amount
    if payer.money <= 0:
        _bankrupt(g, payer)


def _bankrupt(g: GameState, p: Player):
    p.bankrupt = True
    _log(g, f"{p.name} объявлен банкротом!")
    _check_winner(g)


def _check_winner(g: GameState):
    active = [p for p in g.players if not p.bankrupt]
    if len(active) == 1:
        g.winner = active[0].id
        g.status = "finished"
        _log(g, f"Игра окончена! Победитель: {active[0].name}")


def _draw_card(g: GameState, p: Player, deck_type: str) -> dict:
    if deck_type == "chance":
        if not g.chance_deck:
            c, _ = make_decks()
            g.chance_deck = c
        card = g.chance_deck.pop(0)
        g.chance_deck.append(card)  # reshuffle to end
    else:
        if not g.chest_deck:
            _, ch = make_decks()
            g.chest_deck = ch
        card = g.chest_deck.pop(0)
        g.chest_deck.append(card)

    _log(g, f"Карта: {card['text']}")
    _apply_card(g, p, card)
    return _state_snapshot(g)


def _apply_card(g: GameState, p: Player, card: dict):
    t = card["type"]
    if t == "move":
        dest = card["dest"]
        if dest < p.position:
            p.money += GO_BONUS
            _log(g, f"{p.name} прошёл СТАРТ, получил {GO_BONUS}₽.")
        p.position = dest
        if dest != 10:  # not jail visit
            _land_on(g, p)
        else:
            g.phase = "end_turn"

    elif t == "move_back":
        steps = card["steps"]
        p.position = (p.position - steps) % 40
        _land_on(g, p)

    elif t == "move_rr":
        # Nearest railroad
        nearest = _nearest(p.position, RAILROAD_IDS)
        if nearest < p.position:
            p.money += GO_BONUS
        p.position = nearest
        owner = _find_owner(g, nearest)
        if owner and owner.id != p.id:
            rent = _calc_rent(g, nearest, owner, g.dice) * 2
            _pay(g, p, rent, owner)
            _log(g, f"{p.name} заплатил двойную аренду {rent}₽.")
        elif owner is None:
            g.phase = "buy_decision"
            g.pending = {"position": nearest, "price": BOARD[nearest].price}
        else:
            g.phase = "end_turn"

    elif t == "move_ut":
        nearest = _nearest(p.position, UTILITY_IDS)
        if nearest < p.position:
            p.money += GO_BONUS
        p.position = nearest
        rent = 10 * (g.dice[0] + g.dice[1])
        owner = _find_owner(g, nearest)
        if owner and owner.id != p.id:
            _pay(g, p, rent, owner)
            _log(g, f"{p.name} заплатил {rent}₽ за коммунальные услуги.")
        elif owner is None:
            g.phase = "buy_decision"
            g.pending = {"position": nearest, "price": BOARD[nearest].price}
        else:
            g.phase = "end_turn"

    elif t == "jail":
        _send_to_jail(g, p)
        g.phase = "end_turn"

    elif t == "jail_free":
        p.jail_free_cards += 1
        g.phase = "end_turn"

    elif t == "money":
        p.money += card["amount"]
        g.phase = "end_turn"

    elif t == "pay":
        _pay(g, p, card["amount"], None)
        g.phase = "end_turn"

    elif t == "pay_each":
        amount = card["amount"]
        for other in g.players:
            if other.id != p.id and not other.bankrupt:
                _pay(g, other, amount, p)
        g.phase = "end_turn"

    elif t == "collect_each":
        amount = card["amount"]
        for other in g.players:
            if other.id != p.id and not other.bankrupt:
                _pay(g, other, amount, p)
        g.phase = "end_turn"

    elif t == "pay_repairs":
        total = 0
        for pos, prop in p.properties.items():
            if prop.houses < 5:
                total += prop.houses * card["house_cost"]
            else:
                total += card["hotel_cost"]
        _pay(g, p, total, None)
        g.phase = "end_turn"


def _nearest(pos: int, candidates: list[int]) -> int:
    best = candidates[0]
    best_dist = (candidates[0] - pos) % 40
    for c in candidates[1:]:
        d = (c - pos) % 40
        if d < best_dist:
            best_dist = d
            best = c
    return best


def buy_property(g: GameState, player_id: str) -> dict:
    p = current_player(g)
    if p.id != player_id:
        return {"error": "Не ваш ход"}
    if g.phase != "buy_decision":
        return {"error": "Нет предложения о покупке"}
    pos = g.pending["position"]
    price = g.pending["price"]
    if p.money < price:
        return {"error": "Недостаточно денег"}
    p.money -= price
    p.properties[pos] = OwnedProperty(position=pos)
    _log(g, f"{p.name} купил «{BOARD[pos].name}» за {price}₽.")
    g.phase = "end_turn"
    g.pending = {}
    return _state_snapshot(g)


def decline_buy(g: GameState, player_id: str) -> dict:
    p = current_player(g)
    if p.id != player_id:
        return {"error": "Не ваш ход"}
    g.phase = "end_turn"
    g.pending = {}
    return _state_snapshot(g)


def build_house(g: GameState, player_id: str, position: int) -> dict:
    p = current_player(g)
    if p.id != player_id:
        return {"error": "Не ваш ход"}
    if position not in p.properties:
        return {"error": "Это не ваша собственность"}
    space = BOARD[position]
    if space.type != "property":
        return {"error": "Здесь нельзя строить"}
    if not _has_monopoly(p, space.color):
        return {"error": "Нужна монополия на этот район"}
    prop = p.properties[position]
    if prop.mortgaged:
        return {"error": "Собственность заложена"}
    if prop.houses >= 5:
        return {"error": "Уже есть отель"}
    cost = space.house_cost
    if p.money < cost:
        return {"error": "Недостаточно денег"}
    p.money -= cost
    prop.houses += 1
    kind = "отель" if prop.houses == 5 else f"{prop.houses} дом(а)"
    _log(g, f"{p.name} построил {kind} на «{space.name}».")
    return _state_snapshot(g)


def sell_house(g: GameState, player_id: str, position: int) -> dict:
    p = current_player(g)
    if p.id != player_id:
        return {"error": "Не ваш ход"}
    if position not in p.properties:
        return {"error": "Это не ваша собственность"}
    prop = p.properties[position]
    if prop.houses <= 0:
        return {"error": "Нечего продавать"}
    space = BOARD[position]
    p.money += space.house_cost // 2
    prop.houses -= 1
    _log(g, f"{p.name} продал постройку на «{space.name}».")
    return _state_snapshot(g)


def mortgage_property(g: GameState, player_id: str, position: int) -> dict:
    p = current_player(g)
    if p.id != player_id:
        return {"error": "Не ваш ход"}
    if position not in p.properties:
        return {"error": "Это не ваша собственность"}
    prop = p.properties[position]
    if prop.mortgaged:
        return {"error": "Уже заложено"}
    if prop.houses > 0:
        return {"error": "Сначала продайте постройки"}
    space = BOARD[position]
    p.money += space.mortgage_value
    prop.mortgaged = True
    _log(g, f"{p.name} заложил «{space.name}» за {space.mortgage_value}₽.")
    return _state_snapshot(g)


def unmortgage_property(g: GameState, player_id: str, position: int) -> dict:
    p = current_player(g)
    if p.id != player_id:
        return {"error": "Не ваш ход"}
    if position not in p.properties:
        return {"error": "Это не ваша собственность"}
    prop = p.properties[position]
    if not prop.mortgaged:
        return {"error": "Не заложено"}
    space = BOARD[position]
    cost = int(space.mortgage_value * 1.1)
    if p.money < cost:
        return {"error": "Недостаточно денег"}
    p.money -= cost
    prop.mortgaged = False
    _log(g, f"{p.name} выкупил «{space.name}» за {cost}₽.")
    return _state_snapshot(g)


def end_turn(g: GameState, player_id: str) -> dict:
    p = current_player(g)
    if p.id != player_id:
        return {"error": "Не ваш ход"}
    if g.phase != "end_turn":
        return {"error": "Нельзя завершить ход сейчас"}
    _next_turn(g)
    return _state_snapshot(g)


def _next_turn(g: GameState):
    # Skip bankrupt players
    active = [i for i, p in enumerate(g.players) if not p.bankrupt]
    if not active:
        return
    cur = g.current_player_idx
    next_candidates = [i for i in active if i > cur] + [i for i in active if i <= cur]
    next_idx = next_candidates[0] if next_candidates else active[0]
    if next_idx == cur:
        # All others bankrupt
        return
    g.current_player_idx = next_idx
    g.dice_rolled = False
    g.phase = "roll"
    g.dice = (0, 0)
    g.pending = {}
    _log(g, f"Ходит: {g.players[next_idx].name}")


# ── AI turn ───────────────────────────────────────────────────────────────────

def ai_turn(g: GameState) -> list[dict]:
    """Execute full turn for AI player. Returns list of state snapshots."""
    snapshots = []
    p = current_player(g)
    if not p.is_ai or g.phase not in ("roll", "end_turn"):
        return snapshots

    # Jail: pay bail if has enough money
    if p.in_jail and p.money > 200:
        pay_jail_bail(g)

    # Roll until phase is end_turn or buy_decision
    for _ in range(3):
        if g.phase == "roll" and not g.dice_rolled:
            snap = roll_dice(g)
            snapshots.append(snap)

        if g.phase == "buy_decision":
            pos = g.pending.get("position")
            price = g.pending.get("price", 0)
            # Buy if we can afford it and it looks good
            if p.money >= price + 100:
                snap = buy_property(g, p.id)
            else:
                snap = decline_buy(g, p.id)
            snapshots.append(snap)

        if g.phase == "end_turn":
            break

    # Try to build houses if monopoly
    if g.phase == "end_turn":
        for color in COLOR_GROUPS:
            if _has_monopoly(p, color):
                for pos in PROPERTY_IDS:
                    space = BOARD[pos]
                    if space.color == color and pos in p.properties:
                        prop = p.properties[pos]
                        if prop.houses < 4 and p.money > 300:
                            build_house(g, p.id, pos)

    if g.phase == "end_turn":
        snap = end_turn(g, p.id)
        snapshots.append(snap)

    return snapshots


# ── State snapshot for JSON ───────────────────────────────────────────────────

def _state_snapshot(g: GameState) -> dict:
    return {
        "game_id": g.game_id,
        "status": g.status,
        "phase": g.phase,
        "current_player_idx": g.current_player_idx,
        "dice": list(g.dice),
        "dice_rolled": g.dice_rolled,
        "pending": g.pending,
        "winner": g.winner,
        "log": g.log[-10:],
        "players": [_player_dict(p) for p in g.players],
    }


def _player_dict(p: Player) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "is_ai": p.is_ai,
        "money": p.money,
        "position": p.position,
        "in_jail": p.in_jail,
        "jail_turns": p.jail_turns,
        "jail_free_cards": p.jail_free_cards,
        "bankrupt": p.bankrupt,
        "color": p.color,
        "properties": {
            str(pos): {"houses": prop.houses, "mortgaged": prop.mortgaged}
            for pos, prop in p.properties.items()
        },
    }


def lobby_snapshot() -> dict:
    return {"open_games": list_open_games()}
