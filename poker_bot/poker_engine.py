"""Texas Hold'em Poker Engine — Heads-Up (1v1)"""

import random
from typing import List, Optional

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
SUITS = ['h', 'd', 'c', 's']
FULL_DECK = [r + s for r in RANKS for s in SUITS]


class PokerGame:
    """
    Heads-Up Texas Hold'em state machine.
    Cards are represented as 2-char strings like 'As', 'Td', '2h'.
    """

    def __init__(self, starting_stack: int = 3000, small_blind: int = 50):
        self.starting_stack = starting_stack
        self.small_blind = small_blind
        self.big_blind = small_blind * 2

        self.player_stack = starting_stack
        self.ai_stack = starting_stack
        self.hand_num = 0
        self.total_hands = 0

        self.hand: Optional[dict] = None  # current hand state

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def is_game_over(self) -> bool:
        return self.player_stack <= 0 or self.ai_stack <= 0

    def start_new_hand(self) -> dict:
        if self.is_game_over():
            return {"error": "Game is over"}

        self.hand_num += 1
        self.total_hands += 1

        # Alternate dealer/SB:  odd hands → player is SB, even → AI is SB
        player_is_sb = (self.hand_num % 2 == 1)
        sb_player = 'player' if player_is_sb else 'ai'
        bb_player = 'ai' if player_is_sb else 'player'

        # Shuffle & deal
        deck = FULL_DECK.copy()
        random.shuffle(deck)
        player_cards = [deck[0], deck[1]]
        ai_cards = [deck[2], deck[3]]
        remaining_deck = deck[4:]

        # Post blinds (capped by stack)
        sb_amount = min(self.small_blind,
                        self.player_stack if sb_player == 'player' else self.ai_stack)
        bb_amount = min(self.big_blind,
                        self.ai_stack if bb_player == 'ai' else self.player_stack)

        if sb_player == 'player':
            self.player_stack -= sb_amount
            self.ai_stack -= bb_amount
            player_bet = sb_amount
            ai_bet = bb_amount
        else:
            self.ai_stack -= sb_amount
            self.player_stack -= bb_amount
            ai_bet = sb_amount
            player_bet = bb_amount

        current_bet = max(player_bet, ai_bet)

        self.hand = {
            'phase': 'preflop',
            'deck': remaining_deck,
            'player_cards': player_cards,
            'ai_cards': ai_cards,
            'community': [],
            'pot': sb_amount + bb_amount,
            # per-street committed amounts
            'player_bet': player_bet,
            'ai_bet': ai_bet,
            # current call level
            'current_bet': current_bet,
            'last_raise': self.big_blind,
            # who acts next
            'to_act': sb_player,   # SB acts first pre-flop in HU
            'sb_player': sb_player,
            'bb_player': bb_player,
            # preflop: after SB limps, BB gets option
            'bb_has_acted': False,
            'street_checks': 0,
            # result
            'winner': None,
            'ended_by': None,
            'ai_cards_revealed': False,
            'player_hand_name': None,
            'ai_hand_name': None,
            'actions': [
                f"{sb_player}: posts small blind {sb_amount}",
                f"{bb_player}: posts big blind {bb_amount}",
            ],
        }

        return self.get_state()

    def get_state(self, include_ai_cards: bool = False) -> dict:
        """Return a JSON-serialisable snapshot for the frontend."""
        if self.hand is None:
            return {
                'phase': 'waiting',
                'player_stack': self.player_stack,
                'ai_stack': self.ai_stack,
                'hand_num': self.hand_num,
                'game_over': self.is_game_over(),
            }

        h = self.hand
        reveal = include_ai_cards or h.get('ai_cards_revealed', False)

        to_call = 0
        min_raise = self.big_blind
        pot_raise = self.big_blind

        if h['to_act']:
            actor = h['to_act']
            actor_bet = h[f'{actor}_bet']
            actor_stack = self.player_stack if actor == 'player' else self.ai_stack
            to_call = min(max(0, h['current_bet'] - actor_bet), actor_stack)
            min_raise = h['current_bet'] + h['last_raise']
            pot_raise = h['pot'] + to_call + h['current_bet']
            pot_raise = min(pot_raise, actor_bet + actor_stack)
            min_raise = min(min_raise, actor_bet + actor_stack)

        return {
            'phase': h['phase'],
            'player_cards': h['player_cards'],
            'ai_cards': h['ai_cards'] if reveal else ['back', 'back'],
            'ai_cards_actual': h['ai_cards'],
            'community': h['community'],
            'pot': h['pot'],
            'player_stack': self.player_stack,
            'ai_stack': self.ai_stack,
            'player_bet': h['player_bet'],
            'ai_bet': h['ai_bet'],
            'current_bet': h['current_bet'],
            'to_act': h['to_act'],
            'to_call': to_call,
            'min_raise': min_raise,
            'pot_raise': pot_raise,
            'hand_num': self.hand_num,
            'dealer': h['sb_player'],
            'actions': h['actions'][-8:],
            'winner': h.get('winner'),
            'ended_by': h.get('ended_by'),
            'player_hand_name': h.get('player_hand_name'),
            'ai_hand_name': h.get('ai_hand_name'),
            'game_over': self.is_game_over(),
            'ai_cards_revealed': h.get('ai_cards_revealed', False),
            'small_blind': self.small_blind,
            'big_blind': self.big_blind,
        }

    def apply_action(self, actor: str, action: str, raise_to: int = 0) -> dict:
        """
        Apply fold / check / call / raise.
        raise_to = total amount actor commits this street (not raise-by size).
        Returns updated game state dict.
        """
        h = self.hand

        if h is None:
            return {"error": "No active hand"}
        if h['to_act'] != actor:
            return {"error": f"Not {actor}'s turn"}
        if h.get('winner'):
            return {"error": "Hand already finished"}

        other = 'ai' if actor == 'player' else 'player'
        actor_stack = self.player_stack if actor == 'player' else self.ai_stack
        actor_bet = h[f'{actor}_bet']
        to_call = min(max(0, h['current_bet'] - actor_bet), actor_stack)

        # ── FOLD ──────────────────────────────────────────────────────────
        if action == 'fold':
            h['to_act'] = None
            h['winner'] = other
            h['ended_by'] = 'fold'
            h['actions'].append(f"{actor}: folds")
            return self._finish_hand()

        # ── CHECK ─────────────────────────────────────────────────────────
        elif action == 'check':
            if to_call > 0:
                return {"error": "Cannot check — must call or fold"}
            h['actions'].append(f"{actor}: checks")
            h['street_checks'] += 1
            if h['street_checks'] >= 2:
                h['to_act'] = None
                return self._advance_street()
            else:
                h['to_act'] = other

        # ── CALL ──────────────────────────────────────────────────────────
        elif action == 'call':
            if to_call == 0:
                # Treat as check
                return self.apply_action(actor, 'check', 0)

            if actor == 'player':
                self.player_stack -= to_call
            else:
                self.ai_stack -= to_call

            h[f'{actor}_bet'] += to_call
            h['pot'] += to_call

            is_all_in_call = (
                (actor == 'player' and self.player_stack == 0) or
                (actor == 'ai' and self.ai_stack == 0)
            )
            label = "calls all-in" if is_all_in_call else "calls"
            h['actions'].append(f"{actor}: {label} {to_call}")

            # Preflop special: SB limps → BB gets option
            if (h['phase'] == 'preflop'
                    and actor == h['sb_player']
                    and not h['bb_has_acted']
                    and h['player_bet'] == h['ai_bet']):
                h['bb_has_acted'] = True
                h['to_act'] = h['bb_player']
            else:
                h['to_act'] = None
                return self._advance_street()

        # ── RAISE ─────────────────────────────────────────────────────────
        elif action == 'raise':
            min_raise_to = h['current_bet'] + h['last_raise']
            max_raise_to = actor_bet + actor_stack   # all-in

            if raise_to <= 0:
                raise_to = min_raise_to

            raise_to = max(raise_to, min_raise_to)
            raise_to = min(raise_to, max_raise_to)

            additional = raise_to - actor_bet
            if actor == 'player':
                self.player_stack -= additional
            else:
                self.ai_stack -= additional

            h['last_raise'] = raise_to - h['current_bet']
            h['current_bet'] = raise_to
            h[f'{actor}_bet'] = raise_to
            h['pot'] += additional
            h['street_checks'] = 0
            h['bb_has_acted'] = True
            h['to_act'] = other

            is_all_in = (
                (actor == 'player' and self.player_stack == 0) or
                (actor == 'ai' and self.ai_stack == 0)
            )
            label = "raises all-in to" if is_all_in else "raises to"
            h['actions'].append(f"{actor}: {label} {raise_to}")

        else:
            return {"error": f"Unknown action: {action}"}

        # ── Post-action: handle all-in run-outs ───────────────────────────
        if h['to_act'] is not None:
            next_stack = self.player_stack if h['to_act'] == 'player' else self.ai_stack
            next_bet = h[f"{h['to_act']}_bet"]
            # If next actor is all-in and bets are already matched, advance
            if next_stack == 0 and next_bet >= h['current_bet']:
                h['to_act'] = None
                return self._advance_street()

        if self.player_stack == 0 and self.ai_stack == 0:
            h['to_act'] = None
            return self._run_out_board()

        return self.get_state()

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _advance_street(self) -> dict:
        h = self.hand

        # Reset street-level bets
        h['player_bet'] = 0
        h['ai_bet'] = 0
        h['current_bet'] = 0
        h['last_raise'] = self.big_blind
        h['street_checks'] = 0
        h['bb_has_acted'] = True  # only matters preflop

        phase = h['phase']

        if phase == 'preflop':
            h['community'] = h['deck'][:3]
            h['deck'] = h['deck'][3:]
            h['phase'] = 'flop'
        elif phase == 'flop':
            h['community'].append(h['deck'][0])
            h['deck'] = h['deck'][1:]
            h['phase'] = 'turn'
        elif phase == 'turn':
            h['community'].append(h['deck'][0])
            h['deck'] = h['deck'][1:]
            h['phase'] = 'river'
        elif phase == 'river':
            return self._showdown()

        # Post-flop: non-dealer (BB) acts first
        h['to_act'] = h['bb_player']

        # If one player is all-in, skip betting and run out board
        if self.player_stack == 0 or self.ai_stack == 0:
            h['to_act'] = None
            return self._run_out_board()

        return self.get_state()

    def _run_out_board(self) -> dict:
        """Deal remaining community cards when one or both players are all-in."""
        h = self.hand
        while len(h['community']) < 5 and h['deck']:
            h['community'].append(h['deck'].pop(0))
        return self._showdown()

    def _showdown(self) -> dict:
        h = self.hand
        h['phase'] = 'showdown'
        h['ai_cards_revealed'] = True

        try:
            from treys import Card as TCard, Evaluator
            evaluator = Evaluator()

            def to_treys(cards):
                return [TCard.new(c) for c in cards]

            board = to_treys(h['community'])
            player_hand = to_treys(h['player_cards'])
            ai_hand = to_treys(h['ai_cards'])

            p_score = evaluator.evaluate(board, player_hand)
            a_score = evaluator.evaluate(board, ai_hand)

            h['player_hand_name'] = evaluator.class_to_string(
                evaluator.get_rank_class(p_score))
            h['ai_hand_name'] = evaluator.class_to_string(
                evaluator.get_rank_class(a_score))

            if p_score < a_score:    # lower = better in treys
                h['winner'] = 'player'
            elif a_score < p_score:
                h['winner'] = 'ai'
            else:
                h['winner'] = 'tie'

        except Exception:
            h['winner'] = 'tie'
            h['player_hand_name'] = 'Unknown'
            h['ai_hand_name'] = 'Unknown'

        h['ended_by'] = 'showdown'
        return self._finish_hand()

    def _finish_hand(self) -> dict:
        h = self.hand
        winner = h['winner']
        pot = h['pot']

        if winner == 'player':
            self.player_stack += pot
            h['actions'].append(f"Player wins {pot} chips")
        elif winner == 'ai':
            self.ai_stack += pot
            h['actions'].append(f"AI wins {pot} chips")
        elif winner == 'tie':
            each = pot // 2
            self.player_stack += each + (pot % 2)
            self.ai_stack += each
            h['actions'].append(f"Split pot — {each} each")

        h['to_act'] = None
        return self.get_state(include_ai_cards=True)

    # ------------------------------------------------------------------ #
    #  AI helper                                                           #
    # ------------------------------------------------------------------ #

    def get_ai_hand_info(self) -> dict:
        """Return the state the AI player needs to make its decision."""
        if not self.hand:
            return {}
        h = self.hand
        actor_bet = h['ai_bet']
        to_call = min(max(0, h['current_bet'] - actor_bet), self.ai_stack)
        return {
            'ai_cards': h['ai_cards'],
            'player_cards': h['player_cards'],
            'community': h['community'],
            'pot': h['pot'],
            'player_bet': h['player_bet'],
            'ai_bet': h['ai_bet'],
            'current_bet': h['current_bet'],
            'last_raise': h['last_raise'],
            'to_call': to_call,
            'player_stack': self.player_stack,
            'ai_stack': self.ai_stack,
            'phase': h['phase'],
            'position': 'dealer' if h['sb_player'] == 'ai' else 'non-dealer',
            'actions': h['actions'][-8:],
        }

    # ------------------------------------------------------------------ #
    #  Persistence                                                         #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            'player_stack': self.player_stack,
            'ai_stack': self.ai_stack,
            'hand_num': self.hand_num,
            'total_hands': self.total_hands,
            'starting_stack': self.starting_stack,
            'small_blind': self.small_blind,
            'hand': self.hand,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PokerGame':
        game = cls(data['starting_stack'], data['small_blind'])
        game.player_stack = data['player_stack']
        game.ai_stack = data['ai_stack']
        game.hand_num = data['hand_num']
        game.total_hands = data['total_hands']
        game.hand = data.get('hand')
        return game
