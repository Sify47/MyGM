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

        ✅ FIX #1: نستخدم used_ids عشان مفيش مصارع يتكرر
        في أكتر من match في نفس الليلة.

        The AI uses its own roster so both promotions can grow independently.
        """
        show = Show(
            week=state.current_week,
            name=f"{state.ai_name} Weekly",
            is_ple=False,
        )

        # ─── نجيب المتاحين مرتبين حسب القوة ───
        roster = sorted(
            state.ai_roster,
            key=lambda w: w.popularity + w.ring_skill,
            reverse=True,
        )
        available = [w for w in roster if w.is_available()][:12]

        if len(available) < 4:
            # fallback: نستخدم أي حد متاح من غير فلتر
            available = [w for w in roster if w.is_available()]
            if len(available) < 4:
                # مفيش متاحين كفاية → كارت فاضي
                return show

        self.rng.shuffle(available)

        # ✅ FIX #1: used_ids tracking
        used_ids: set[int] = set()

        def pick_fresh(count: int) -> list:
            """
            يرجّع list من المصارعين اللي مش مستخدمين لسه.
            لو مفيش كفاية → يرجّع None.
            """
            fresh = [w for w in available if w.id not in used_ids]
            if len(fresh) < count:
                return None
            return fresh[:count]

        # ----- Match 1: Opener (midcard) -----
        opener = pick_fresh(2)
        if opener:
            show.matches.append(
                Match(
                    match_type=MatchType.SINGLES,
                    participant_ids=[opener[0].id, opener[1].id],
                    importance=MatchImportance.OPENER,
                )
            )
            used_ids.update(w.id for w in opener)

        # ----- Match 2: Midcard -----
        midcard = pick_fresh(2)
        if midcard:
            show.matches.append(
                Match(
                    match_type=MatchType.SINGLES,
                    participant_ids=[midcard[0].id, midcard[1].id],
                    importance=MatchImportance.MIDCARD,
                )
            )
            used_ids.update(w.id for w in midcard)

        # ----- Match 3: Upper card (Triple Threat) -----
        upper = pick_fresh(3)
        if upper:
            show.matches.append(
                Match(
                    match_type=MatchType.TRIPLE_THREAT,
                    participant_ids=[w.id for w in upper],
                    importance=MatchImportance.UPPER_CARD,
                )
            )
            used_ids.update(w.id for w in upper)

        # ----- Main event: top 2 من اللي لسه متاحين -----
        remaining = [w for w in available if w.id not in used_ids]
        if len(remaining) >= 2:
            # نرتب حسب الشعبية وناخد أعلى 2
            top = sorted(remaining, key=lambda w: w.popularity, reverse=True)[:2]

            # نحاول نخليها Face vs Heel
            if top[0].alignment == top[1].alignment:
                for w in remaining:
                    if w.id in (top[0].id, top[1].id):
                        continue
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
            used_ids.update(w.id for w in top)

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
