"""
Rivalry Engine - manages feuds between wrestlers.
"""

from __future__ import annotations

import random

from config import Config
from core.enums import RivalryStage
from core.constants import clamp
from domain.models.rivalry import Rivalry
from domain.models.game_state import GameState


class RivalryEngine:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    # =========================================================
    # CREATE / FIND
    # =========================================================

    def create_or_get_rivalry(
        self,
        a_id: str,
        b_id: str,
        state: GameState,
    ) -> Rivalry:
        """Return existing rivalry between two wrestlers, or create one."""
        existing = state.find_rivalry_between(a_id, b_id)
        if existing:
            return existing

        rivalry = Rivalry(wrestler_a_id=a_id, wrestler_b_id=b_id, heat=0)
        state.rivalries.append(rivalry)

        a = state.get_wrestler(a_id)
        b = state.get_wrestler(b_id)
        if a and b:
            a.current_rivalry_id = rivalry.id
            b.current_rivalry_id = rivalry.id

        return rivalry

    # =========================================================
    # ADVANCE HEAT
    # =========================================================

    def apply_event(
        self,
        rivalry: Rivalry,
        event_type: str,
        state: GameState,
    ) -> None:
        """
        event_type in:
        'promo' | 'interference' | 'tag' | 'singles' | 'betrayal'
        """
        mapping = {
            "promo": Config.RIVALRY_HEAT_PROMO,
            "interference": Config.RIVALRY_HEAT_INTERFERENCE,
            "tag": Config.RIVALRY_HEAT_TAG,
            "singles": Config.RIVALRY_HEAT_SINGLES,
            "betrayal": Config.RIVALRY_HEAT_BETRAYAL,
        }
        delta = mapping.get(event_type, 0)
        rivalry.add_heat(delta, state.current_week, event_type)

    # =========================================================
    # WEEKLY UPDATE
    # =========================================================

    def weekly_update(self, state: GameState) -> list[str]:
        """
        Called at the end of every week.
        - Increments weeks_active
        - Applies decay to rivalries with no interaction
        - Marks rivalries as ENDED if heat drops too low
        Returns list of news strings.
        """
        news = []
        for rivalry in state.rivalries:
            if rivalry.stage == RivalryStage.ENDED:
                continue

            # Did this rivalry get action this week?
            had_action = any(h["week"] == state.current_week for h in rivalry.history)

            if had_action:
                rivalry.weeks_active += 1
            else:
                rivalry.add_heat(
                    Config.RIVALRY_DECAY_NO_INTERACTION,
                    state.current_week,
                    "no_interaction",
                )
                # Only age if it's already a real rivalry
                if rivalry.heat > 0:
                    rivalry.weeks_active += 1

            # End condition
            if rivalry.heat <= 5 and rivalry.weeks_active >= 2:
                self.end_rivalry(rivalry, state)
                a = state.get_wrestler(rivalry.wrestler_a_id)
                b = state.get_wrestler(rivalry.wrestler_b_id)
                if a and b:
                    news.append(
                        f"Rivalry between {a.name} and {b.name} has cooled off."
                    )

        return news

    def end_rivalry(self, rivalry: Rivalry, state: GameState) -> None:
        rivalry.heat = 0
        a = state.get_wrestler(rivalry.wrestler_a_id)
        b = state.get_wrestler(rivalry.wrestler_b_id)
        if a and a.current_rivalry_id == rivalry.id:
            a.current_rivalry_id = None
        if b and b.current_rivalry_id == rivalry.id:
            b.current_rivalry_id = None

    # =========================================================
    # AUTO DETECT
    # =========================================================

    def maybe_create_rivalry_from_match(
        self,
        winner_id: str,
        loser_id: str,
        state: GameState,
    ) -> Rivalry | None:
        """
        After a match, small chance to spark a rivalry
        based on personality traits.
        """
        winner = state.get_wrestler(winner_id)
        loser = state.get_wrestler(loser_id)
        if not winner or not loser:
            return None

        # Base chance
        chance = 0.25

        # Traits increase chance
        aggressive_traits = {"Ego", "Bitter", "Arrogant", "Veteran", "Schemer"}
        if any(t in aggressive_traits for t in winner.traits + loser.traits):
            chance += 0.15

        # If both are heels or both faces, more likely to clash
        if winner.alignment == loser.alignment:
            chance += 0.10

        if self.rng.random() < chance:
            rivalry = self.create_or_get_rivalry(winner_id, loser_id, state)
            self.apply_event(rivalry, "singles", state)
            return rivalry
        return None
