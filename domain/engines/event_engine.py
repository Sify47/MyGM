"""
Event Engine - generates weekly random events.
"""

from __future__ import annotations

import random

from config import Config
from core.enums import EventSeverity
from domain.models.game_state import GameState


class EventEngine:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    # =========================================================
    # ROLL
    # =========================================================

    def roll_severity(self) -> EventSeverity:
        r = self.rng.random()
        if r < Config.EVENT_NONE:
            return EventSeverity.NONE
        if r < Config.EVENT_NONE + Config.EVENT_MINOR:
            return EventSeverity.MINOR
        if r < Config.EVENT_NONE + Config.EVENT_MINOR + Config.EVENT_MAJOR:
            return EventSeverity.MAJOR
        return EventSeverity.OMG

    # =========================================================
    # GENERATE
    # =========================================================

    def generate(self, state: GameState) -> dict | None:
        severity = self.roll_severity()
        if severity == EventSeverity.NONE:
            return None

        if severity == EventSeverity.MINOR:
            return self._minor_event(state)
        if severity == EventSeverity.MAJOR:
            return self._major_event(state)
        return self._omg_event(state)

    # =========================================================
    # MINOR EVENTS
    # =========================================================

    def _minor_event(self, state: GameState) -> dict | None:
        pool = [
            self._event_bad_promo,
            self._event_great_promo,
            self._event_locker_room,
            self._event_fan_favorite,
        ]
        handler = self.rng.choice(pool)
        return handler(state)

    def _event_bad_promo(self, state: GameState) -> dict:
        w = self._random_roster(state)
        if not w:
            return None
        w.adjust_popularity(-2)
        w.adjust_morale(-3)
        text = f"🎤 {w.name} delivered a weak promo. Popularity -2."
        state.add_news(text)
        return {"type": "bad_promo", "wrestler_id": w.id, "text": text}

    def _event_great_promo(self, state: GameState) -> dict:
        w = self._random_roster(state)
        if not w:
            return None
        bonus = 3 if w.mic_skill >= 75 else 1
        w.adjust_popularity(bonus)
        text = f"🎤 {w.name} cut a great promo! Popularity +{bonus}."
        state.add_news(text)
        return {"type": "great_promo", "wrestler_id": w.id, "text": text}

    def _event_locker_room(self, state: GameState) -> dict:
        a = self._random_roster(state)
        b = self._random_roster(state, exclude=[a.id] if a else [])
        if not a or not b:
            return None
        a.adjust_morale(-5)
        b.adjust_morale(-5)
        text = f"🔥 Locker room tension between {a.name} and {b.name}."
        state.add_news(text)
        return {"type": "locker_room", "text": text}

    def _event_fan_favorite(self, state: GameState) -> dict:
        w = self._random_roster(state)
        if not w:
            return None
        w.adjust_popularity(2)
        w.adjust_morale(3)
        text = f"❤️ The crowd is chanting for {w.name}!"
        state.add_news(text)
        return {"type": "fan_favorite", "wrestler_id": w.id, "text": text}

    # =========================================================
    # MAJOR EVENTS
    # =========================================================

    def _major_event(self, state: GameState) -> dict | None:
        pool = [
            self._event_contract_demand,
            self._event_sponsor_offer,
            self._event_backstage_fight,
        ]
        handler = self.rng.choice(pool)
        return handler(state)

    def _event_contract_demand(self, state: GameState) -> dict:
        candidates = [w for w in state.roster if w.morale < 55 or w.popularity > 75]
        if not candidates:
            candidates = state.roster
        w = self.rng.choice(candidates)
        text = f"📝 {w.name} is demanding a bigger role."
        state.add_news(text)
        return {
            "type": "contract_demand",
            "wrestler_id": w.id,
            "text": text,
            "options": ["Give Push", "Negotiate", "Ignore"],
        }

    def _event_sponsor_offer(self, state: GameState) -> dict:
        amount = self.rng.randint(20_000, 60_000)
        state.player_budget += amount
        text = f"💰 A sponsor offers ${amount:,}! Budget increased."
        state.add_news(text)
        return {"type": "sponsor_offer", "amount": amount, "text": text}

    def _event_backstage_fight(self, state: GameState) -> dict:
        a = self._random_roster(state)
        b = self._random_roster(state, exclude=[a.id] if a else [])
        if not a or not b:
            return None
        a.adjust_morale(-8)
        b.adjust_morale(-8)
        a.adjust_popularity(-2)
        b.adjust_popularity(-2)
        text = f"💥 Backstage fight between {a.name} and {b.name}!"
        state.add_news(text)
        return {"type": "backstage_fight", "text": text}

    # =========================================================
    # OMG EVENTS
    # =========================================================

    def _omg_event(self, state: GameState) -> dict | None:
        pool = [
            self._event_injury,
            self._event_surprise_return,
            self._event_major_upset,
        ]
        handler = self.rng.choice(pool)
        return handler(state)

    def _event_injury(self, state: GameState) -> dict | None:
        candidates = [w for w in state.roster if w.health < 70]
        if not candidates:
            candidates = state.roster
        w = self.rng.choice(candidates)
        w.is_injured = True
        w.injury_weeks = self.rng.randint(2, 5)
        w.adjust_morale(-10)
        text = f"🚑 {w.name} is injured! Out for {w.injury_weeks} weeks."
        state.add_news(text)
        return {"type": "injury", "wrestler_id": w.id, "text": text}

    def _event_surprise_return(self, state: GameState) -> dict | None:
        injured = [w for w in state.roster if w.is_injured]
        if not injured:
            return self._event_great_promo(state)
        w = self.rng.choice(injured)
        w.is_injured = False
        w.injury_weeks = 0
        w.adjust_popularity(5)
        text = f"🎉 {w.name} returns from injury! Popularity +5."
        state.add_news(text)
        return {"type": "surprise_return", "wrestler_id": w.id, "text": text}

    def _event_major_upset(self, state: GameState) -> dict | None:
        w = self._random_roster(state)
        if not w:
            return None
        w.adjust_popularity(8)
        w.adjust_morale(10)
        text = f"😱 {w.name} pulled off a career-defining upset!"
        state.add_news(text)
        return {"type": "major_upset", "wrestler_id": w.id, "text": text}

    # =========================================================
    # HELPERS
    # =========================================================

    def _random_roster(
        self,
        state: GameState,
        exclude: list[str] | None = None,
    ):
        exclude = exclude or []
        pool = [w for w in state.roster if w.id not in exclude and w.contract_weeks > 0]
        if not pool:
            return None
        return self.rng.choice(pool)
