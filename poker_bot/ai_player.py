"""
AI Poker Player — Heads-Up Texas Hold'em
Strategy: Monte Carlo hand strength + GTO heuristics + GPT for strategic variety
"""

import random
import json
import asyncio
import os
from typing import List, Optional

from openai import AsyncOpenAI

# ── AI provider config ────────────────────────────────────────────────────────
# Set AI_PROVIDER=google in .env to use Google Gemini; default is openai
_GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
SUITS = ['h', 'd', 'c', 's']
FULL_DECK = [r + s for r in RANKS for s in SUITS]
RANK_IDX = {r: i for i, r in enumerate(RANKS)}

# ──────────────────────────────────────────────────────────────────────────────
#  Pre-flop hand strength table (equity vs random HU opponent, approximate GTO)
# ──────────────────────────────────────────────────────────────────────────────
_PF: dict = {
    # Pocket pairs
    'AA': 0.853, 'KK': 0.823, 'QQ': 0.800, 'JJ': 0.775, 'TT': 0.751,
    '99': 0.721, '88': 0.692, '77': 0.661, '66': 0.633, '55': 0.607,
    '44': 0.581, '33': 0.556, '22': 0.535,
    # Suited connectors / aces
    'AKs': 0.673, 'AQs': 0.660, 'AJs': 0.645, 'ATs': 0.631,
    'A9s': 0.614, 'A8s': 0.600, 'A7s': 0.587, 'A6s': 0.575,
    'A5s': 0.592, 'A4s': 0.578, 'A3s': 0.564, 'A2s': 0.551,
    'KQs': 0.632, 'KJs': 0.618, 'KTs': 0.604, 'K9s': 0.587,
    'QJs': 0.609, 'QTs': 0.596, 'Q9s': 0.578,
    'JTs': 0.599, 'J9s': 0.582, 'T9s': 0.579, '98s': 0.567,
    '87s': 0.555, '76s': 0.545, '65s': 0.535,
    # Offsuit
    'AKo': 0.651, 'AQo': 0.635, 'AJo': 0.618, 'ATo': 0.601,
    'A9o': 0.582, 'A8o': 0.568, 'A7o': 0.554, 'A6o': 0.540,
    'A5o': 0.556, 'A4o': 0.541, 'A3o': 0.527, 'A2o': 0.514,
    'KQo': 0.607, 'KJo': 0.591, 'KTo': 0.574, 'K9o': 0.556,
    'QJo': 0.580, 'QTo': 0.563,
    'JTo': 0.567, 'J9o': 0.549,
    'T9o': 0.543, '98o': 0.529,
}


def _preflop_strength(c1: str, c2: str) -> float:
    r1, s1 = c1[:-1], c1[-1]
    r2, s2 = c2[:-1], c2[-1]
    # Sort higher rank first
    if RANK_IDX[r1] < RANK_IDX[r2]:
        r1, r2 = r2, r1
        s1, s2 = s2, s1
    suited = 's' if s1 == s2 else 'o'
    if r1 == r2:
        key = r1 + r2
        return _PF.get(key, 0.520)
    return _PF.get(f"{r1}{r2}{suited}", _PF.get(f"{r1}{r2}o", 0.480))


def monte_carlo_strength(hole: List[str], community: List[str],
                          n: int = 500) -> float:
    """Win probability via Monte Carlo simulation (lower n for speed)."""
    try:
        from treys import Card as TC, Evaluator
        ev = Evaluator()

        known = set(hole + community)
        remaining = [c for c in FULL_DECK if c not in known]
        cards_needed = 5 - len(community)

        wins = ties = 0.0
        sims = 0

        for _ in range(n):
            random.shuffle(remaining)
            opp = remaining[:2]
            board = community + remaining[2: 2 + cards_needed]

            if len(board) < 3:
                continue
            try:
                b = [TC.new(c) for c in board]
                h = [TC.new(c) for c in hole]
                o = [TC.new(c) for c in opp]
                my = ev.evaluate(b, h)
                their = ev.evaluate(b, o)
                if my < their:
                    wins += 1
                elif my == their:
                    ties += 0.5
                sims += 1
            except Exception:
                continue

        return (wins + ties) / sims if sims > 0 else 0.50
    except Exception:
        return 0.50


# ──────────────────────────────────────────────────────────────────────────────
#  AI Player
# ──────────────────────────────────────────────────────────────────────────────

class AIPlayer:
    def __init__(self):
        provider = os.getenv("AI_PROVIDER", "openai").lower()
        if provider == "google":
            self.client = AsyncOpenAI(
                api_key=os.getenv("GOOGLE_AI_API_KEY", ""),
                base_url=_GOOGLE_BASE_URL,
            )
            self._model = os.getenv("GOOGLE_TEXT_MODEL", "gemini-2.0-flash")
        else:
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
            self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.decisions_made = 0
        self.action_history: List[str] = []   # last ~20 actions for pattern tracking
        self._gpt_every = random.randint(5, 9)  # vary GPT call frequency

    # ── Main entry point ──────────────────────────────────────────────────────

    async def decide(self, info: dict) -> dict:
        """
        info comes from PokerGame.get_ai_hand_info()
        Returns {"action": "fold|check|call|raise", "amount": int}
        """
        self.decisions_made += 1

        phase = info['phase']
        community = info['community']
        hole = info['ai_cards']
        pot = info['pot']
        ai_stack = info['ai_stack']
        to_call = info['to_call']
        current_bet = info['current_bet']
        ai_bet = info['ai_bet']
        last_raise = info.get('last_raise', 100)

        pot_odds = to_call / (pot + to_call) if to_call > 0 else 0.0

        # Hand strength
        if phase == 'preflop' and not community:
            win_rate = _preflop_strength(hole[0], hole[1])
        else:
            sims = 300 if phase in ('flop', 'turn') else 400
            win_rate = monte_carlo_strength(hole, community, n=sims)

        # Decide if GPT call should be made
        use_gpt = (
            self.decisions_made % self._gpt_every == 0
            or (0.38 < win_rate < 0.62 and phase in ('flop', 'turn', 'river')
                and random.random() < 0.45)
        )

        if use_gpt:
            try:
                decision = await self._gpt_decide(info, win_rate, to_call, pot_odds)
                if decision and self._validate(decision, info):
                    self._record(decision['action'])
                    return decision
            except Exception:
                pass  # fall through to algorithmic

        decision = self._algo_decide(info, win_rate, to_call, pot_odds)
        self._record(decision['action'])
        return decision

    # ── Algorithmic (GTO-inspired) ────────────────────────────────────────────

    def _algo_decide(self, info: dict, win_rate: float,
                     to_call: int, pot_odds: float) -> dict:
        pot = info['pot']
        ai_stack = info['ai_stack']
        ai_bet = info['ai_bet']
        current_bet = info['current_bet']
        last_raise = info.get('last_raise', 100)
        position = info['position']   # 'dealer' or 'non-dealer'

        # Positional bonus: dealer has more information, slightly widen range
        pos_adj = 0.04 if position == 'dealer' else -0.02

        # Anti-pattern: if we've been folding too much, force some action
        recent = self.action_history[-6:]
        if recent.count('fold') >= 4:
            pos_adj += 0.15

        # Gaussian noise for mixed strategy
        noise = random.gauss(0, 0.04)
        eff = win_rate + pos_adj + noise

        def raise_to(frac: float) -> int:
            target = current_bet + max(int(pot * frac), last_raise)
            target = max(target, current_bet + last_raise)  # min-raise rule
            return min(target, ai_bet + ai_stack)          # cap at stack

        # ── No bet to face (can check) ─────────────────────────────────
        if to_call == 0:
            if eff > 0.72:
                # Strong: usually bet for value
                if random.random() < 0.80:
                    return {"action": "raise", "amount": raise_to(0.65)}
                return {"action": "check"}

            elif eff > 0.58:
                # Good: mix bet and check
                if random.random() < 0.55:
                    return {"action": "raise", "amount": raise_to(0.45)}
                return {"action": "check"}

            elif eff > 0.44:
                # Marginal: mostly check, occasional bet
                if random.random() < 0.22:
                    return {"action": "raise", "amount": raise_to(0.45)}
                return {"action": "check"}

            else:
                # Weak: mostly check; bluff ~10%
                if random.random() < 0.10:
                    return {"action": "raise", "amount": raise_to(0.60)}
                return {"action": "check"}

        # ── Facing a bet ──────────────────────────────────────────────
        if eff > 0.78:
            # Very strong: raise most of the time
            if random.random() < 0.72:
                return {"action": "raise", "amount": raise_to(0.75)}
            return {"action": "call"}

        elif eff > 0.64:
            # Good hand: call, sometimes raise
            if random.random() < 0.38:
                return {"action": "raise", "amount": raise_to(0.55)}
            return {"action": "call"}

        elif eff > 0.50:
            # Marginal: call if pot odds are right, else fold/bluff-raise
            if eff > pot_odds:
                if random.random() < 0.18:
                    return {"action": "raise", "amount": raise_to(0.65)}
                return {"action": "call"}
            else:
                if random.random() < 0.15:   # bluff
                    return {"action": "raise", "amount": raise_to(0.70)}
                return {"action": "fold"}

        elif eff > 0.35:
            # Weak: usually fold; call if pot odds justify; rare bluff
            if eff > pot_odds and random.random() < 0.35:
                return {"action": "call"}
            if random.random() < 0.10:
                return {"action": "raise", "amount": raise_to(0.75)}
            return {"action": "fold"}

        else:
            # Very weak: fold or bluff
            if random.random() < 0.08:
                return {"action": "raise", "amount": raise_to(0.80)}
            return {"action": "fold"}

    # ── GPT decision ──────────────────────────────────────────────────────────

    async def _gpt_decide(self, info: dict, win_rate: float,
                           to_call: int, pot_odds: float) -> Optional[dict]:
        hole = info['ai_cards']
        community = info['community']
        pot = info['pot']
        ai_stack = info['ai_stack']
        player_stack = info['player_stack']
        current_bet = info['current_bet']
        ai_bet = info['ai_bet']
        last_raise = info.get('last_raise', 100)
        phase = info['phase']
        position = info['position']
        actions = info.get('actions', [])[-6:]

        min_r = current_bet + last_raise
        max_r = ai_bet + ai_stack
        spr = round(min(ai_stack, player_stack) / max(pot, 1), 1)
        recent_pat = self._pattern_summary()

        prompt = (
            f"You're an expert heads-up Texas Hold'em player.\n\n"
            f"YOUR HOLE CARDS: {hole[0]} {hole[1]}\n"
            f"BOARD: {' '.join(community) if community else '(none)'} | Phase: {phase}\n"
            f"POSITION: {position} (dealer=SB)\n"
            f"POT: {pot} | To call: {to_call} | Your stack: {ai_stack} | Opp stack: {player_stack}\n"
            f"Pot odds: {pot_odds:.1%} | Monte Carlo equity: {win_rate:.1%} | SPR: {spr}\n"
            f"Raise range: [{min_r} .. {max_r}]\n"
            f"Recent hand history:\n" + "\n".join(f"  {a}" for a in actions) + "\n"
            f"Your recent action pattern: {recent_pat}\n\n"
            f"Make a strategic decision.\n"
            f"- Avoid predictable patterns.\n"
            f"- Use position and SPR.\n"
            f"- Balance bluffs with value.\n\n"
            f"Respond with JSON only (no markdown):\n"
            f'{{ "action": "fold|check|call|raise", "amount": 0 }}\n'
            f"amount=0 for fold/check/call; for raise, amount = total chips to commit this street."
        )

        resp = await self.client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=80,
            timeout=6.0,
        )

        raw = json.loads(resp.choices[0].message.content)
        action = str(raw.get("action", "call")).lower().strip()
        amount = int(raw.get("amount", 0))

        return {"action": action, "amount": amount}

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _validate(self, decision: dict, info: dict) -> bool:
        action = decision.get("action")
        if action not in ("fold", "check", "call", "raise"):
            return False
        if action == "check" and info['to_call'] > 0:
            decision["action"] = "call"   # fix invalid check
        if action == "raise":
            last_raise = info.get('last_raise', 100)
            min_r = info['current_bet'] + last_raise
            max_r = info['ai_bet'] + info['ai_stack']
            amt = decision.get("amount", 0)
            decision["amount"] = max(min_r, min(amt if amt > 0 else min_r, max_r))
        return True

    def _record(self, action: str):
        self.action_history.append(action)
        if len(self.action_history) > 24:
            self.action_history.pop(0)

    def _pattern_summary(self) -> str:
        last = self.action_history[-8:] if self.action_history else []
        if not last:
            return "no history"
        counts = {a: last.count(a) for a in ('fold', 'call', 'check', 'raise')}
        return ", ".join(f"{k}×{v}" for k, v in counts.items() if v)
