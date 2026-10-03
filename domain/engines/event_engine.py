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
    # WEEKLY GAMEPLAY LAYER
    # =========================================================

    def generate_objective(self, state: GameState) -> dict:
        """Create a short-term goal that changes how the player books."""
        candidates = [
            {
                "id": "great_show",
                "title": "Put on a Great Show",
                "description": "Finish the week with a show rating of 78 or higher.",
                "kind": "SHOW_RATING",
                "target": 78,
                "reward_budget": 75_000,
                "reward_fans": 3_000,
            },
            {
                "id": "profitable_week",
                "title": "Keep the Books Healthy",
                "description": "Finish the week with at least $180,000 profit.",
                "kind": "PROFIT",
                "target": 180_000,
                "reward_budget": 100_000,
                "reward_fans": 1_000,
            },
            {
                "id": "push_a_rookie",
                "title": "Build the Next Star",
                "description": "Book a Rookie in a match this week.",
                "kind": "ROOKIE_BOOKED",
                "target": 1,
                "reward_budget": 40_000,
                "reward_fans": 4_000,
            },
            {
                "id": "champion_main_event",
                "title": "Put the Champion in the Spotlight",
                "description": "Book a current champion in the Main Event.",
                "kind": "CHAMPION_MAIN_EVENT",
                "target": 1,
                "reward_budget": 60_000,
                "reward_fans": 2_000,
            },
        ]
        return dict(self.rng.choice(candidates))

    def generate_decision(self, state: GameState) -> dict:
        """Create a decision with meaningful trade-offs for the current week."""
        candidates = [w for w in state.roster if w.contract_weeks > 0]
        wrestler = self.rng.choice(candidates) if candidates else None
        if wrestler:
            return {
                "id": "role_demand",
                "title": "Locker Room Decision",
                "text": f"{wrestler.name} wants a bigger role this week.",
                "wrestler_id": wrestler.id,
                "options": [
                    {
                        "id": "push",
                        "label": "Give them a Push",
                        "summary": "Popularity +4, Morale +6",
                    },
                    {
                        "id": "bonus",
                        "label": "Offer a Bonus",
                        "summary": "Pay $50,000, Morale +10",
                    },
                    {
                        "id": "ignore",
                        "label": "Ignore the Demand",
                        "summary": "Save money, but Morale -8",
                    },
                ],
            }
        return {
            "id": "sponsor_choice",
            "title": "Sponsor Offer",
            "text": "A sponsor offers money in exchange for a louder presence on your show.",
            "options": [
                {
                    "id": "accept",
                    "label": "Accept",
                    "summary": "Budget +$45,000, Fans -500",
                },
                {
                    "id": "decline",
                    "label": "Decline",
                    "summary": "Keep the show independent",
                },
            ],
        }

    def apply_decision(self, state: GameState, option_id: str) -> dict:
        decision = state.pending_decision
        if not decision:
            return {"ok": False, "reason": "There is no pending decision."}

        valid = {option["id"] for option in decision.get("options", [])}
        if option_id not in valid:
            return {"ok": False, "reason": "Invalid decision option."}

        wrestler = state.get_wrestler(decision.get("wrestler_id"))
        if decision["id"] == "role_demand" and wrestler:
            if option_id == "push":
                wrestler.adjust_popularity(4)
                wrestler.adjust_morale(6)
                text = f"📈 You gave {wrestler.name} a bigger push."
            elif option_id == "bonus":
                state.player_budget -= 50_000
                wrestler.adjust_morale(10)
                text = f"💰 You paid a $50,000 bonus to {wrestler.name}."
            else:
                wrestler.adjust_morale(-8)
                text = f"😤 You ignored {wrestler.name}'s demand. Morale dropped."
        elif decision["id"] == "sponsor_choice" and option_id == "accept":
            state.player_budget += 45_000
            state.player_fans = max(1_000, state.player_fans - 500)
            text = "💰 You accepted the sponsor's offer."
        else:
            text = "🛡️ You kept the show independent."

        state.pending_decision = None
        state.decision_resolved_week = state.current_week
        state.last_decision_result = {"text": text, "option_id": option_id}
        state.add_news(text)
        return {"ok": True, "text": text, "option_id": option_id}

    def evaluate_objective(self, state: GameState) -> dict:
        objective = state.weekly_objective
        show = state.shows[-1] if state.shows else None
        if not objective or not show:
            return {"completed": False, "text": "No weekly objective was active."}

        kind = objective["kind"]
        if kind == "SHOW_RATING":
            completed = show.rating >= objective["target"]
            progress = show.rating
        elif kind == "PROFIT":
            completed = show.revenue - show.expenses >= objective["target"]
            progress = show.revenue - show.expenses
        elif kind == "ROOKIE_BOOKED":
            rookie_ids = {
                w.id
                for w in state.roster
                if "Rookie" in w.traits or "Rising Star" in w.traits
            }
            booked = {pid for match in show.matches for pid in match.participant_ids}
            completed = bool(rookie_ids & booked)
            progress = 1 if completed else 0
        else:
            champion_ids = {w.id for w in state.roster if w.is_champion}
            main = next(
                (m for m in show.matches if m.importance.value == "MAIN_EVENT"), None
            )
            completed = bool(main and champion_ids & set(main.participant_ids))
            progress = 1 if completed else 0

        if completed:
            state.player_budget += objective["reward_budget"]
            state.player_fans += objective["reward_fans"]
            text = (
                f"✅ Objective complete: {objective['title']} "
                f"(+${objective['reward_budget']:,}, +{objective['reward_fans']:,} fans)."
            )
        else:
            text = f"❌ Objective missed: {objective['title']}."
        result = {"completed": completed, "text": text, "progress": progress}
        state.last_objective_result = result
        state.add_news(text)
        return result

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
