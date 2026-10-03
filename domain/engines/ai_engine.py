"""
AI Engine - rule-based decisions for the AI GM.
"""

from __future__ import annotations

import random

from core.enums import (
    MatchType,
    MatchImportance,
    Alignment,
)
from domain.models.match import Match
from domain.models.show import Show
from domain.models.game_state import GameState


class AIEngine:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    # =========================================================
    # MAIN
    # =========================================================

    def book_ai_show(self, state: GameState) -> Show:
        """
        Build a 4-match card for the AI promotion.
        AI keeps its own roster simple: it just reuses the player's
        roster IDs for simulation (MVP shortcut).
        """
        show = Show(
            week=state.current_week,
            name=f"{state.ai_name} Weekly",
            is_ple=False,
        )

        roster = sorted(
            state.roster,
            key=lambda w: w.popularity + w.ring_skill,
            reverse=True,
        )
        # AI picks its top 8 available wrestlers
        available = [w for w in roster if w.is_available()][:8]
        if len(available) < 4:
            available = roster[:4]

        self.rng.shuffle(available)

        # ----- Match 1: Opener (midcard) -----
        show.matches.append(
            Match(
                match_type=MatchType.SINGLES,
                participant_ids=[available[0].id, available[1].id],
                importance=MatchImportance.OPENER,
            )
        )

        # ----- Match 2: Midcard -----
        show.matches.append(
            Match(
                match_type=MatchType.SINGLES,
                participant_ids=[available[2].id, available[3].id],
                importance=MatchImportance.MIDCARD,
            )
        )

        # ----- Match 3: Upper card -----
        if len(available) >= 6:
            show.matches.append(
                Match(
                    match_type=MatchType.TRIPLE_THREAT,
                    participant_ids=[available[4].id, available[5].id, available[0].id],
                    importance=MatchImportance.UPPER_CARD,
                )
            )

        # ----- Main event: top 2 -----
        top = sorted(available, key=lambda w: w.popularity, reverse=True)[:2]
        # Try to make it a face vs heel
        if len(top) == 2 and top[0].alignment == top[1].alignment:
            for w in available[2:]:
                if w.alignment != top[0].alignment:
                    top[1] = w
                    break

        show.matches.append(
            Match(
                match_type=MatchType.SINGLES,
                participant_ids=[top[0].id, top[1].id],
                importance=MatchImportance.MAIN_EVENT,
            )
        )

        return show

    # =========================================================
    # QUICK SIM FOR AI SHOW
    # =========================================================

    def simulate_ai_show(
        self,
        show: Show,
        state: GameState,
        match_engine,
    ) -> int:
        """
        Simulate the AI's show, return its rating.
        AI wrestlers still take health/stamina hits (shared roster for MVP).
        """
        ratings = []
        for m in show.matches:
            result = match_engine.simulate(m, state)
            if "rating" in result:
                ratings.append(result["rating"])

        if not ratings:
            state.ai_last_show_rating = 50
            return 50

        # Main event weighted heavier
        avg = sum(ratings) / len(ratings)
        if len(ratings) >= 2:
            avg = avg * 0.7 + ratings[-1] * 0.3

        state.ai_last_show_rating = int(avg)
        return state.ai_last_show_rating
