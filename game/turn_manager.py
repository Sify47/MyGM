"""
Turn Manager - drives the entire weekly loop.
"""

from __future__ import annotations

import random

from config import Config
from core.enums import MatchImportance
from domain.engines import (
    MatchEngine,
    RivalryEngine,
    EconomyEngine,
    EventEngine,
    AIEngine,
)
from domain.models.game_state import GameState
from domain.models.show import Show
from game.booking_manager import BookingManager
from domain.engines import StoryEngine


class TurnManager:
    def __init__(self, state: GameState, seed: int | None = None):
        self.state = state
        rng = random.Random(seed)

        self.match_engine = MatchEngine(rng)
        self.rivalry_engine = RivalryEngine(rng)
        self.economy_engine = EconomyEngine(rng)
        self.event_engine = EventEngine(rng)
        self.ai_engine = AIEngine(rng)
        self.story_engine = StoryEngine(rng)
        self.booking = BookingManager(state)

    # =========================================================
    # SHOW SIMULATION
    # =========================================================

    def simulate_show(self, show: Show) -> dict:
        """
        Run the player's show:
        - simulate each match
        - compute show rating
        - run economy
        - update rivalries
        """
        match_results = []
        for match in show.matches:
            result = self.match_engine.simulate(match, self.state)
            match_results.append(result)

            # Rivalry heat from match
            if match.rivalry_id:
                rivalry = self.state.get_rivalry(match.rivalry_id)
                if rivalry:
                    self.rivalry_engine.apply_event(rivalry, "singles", self.state)

            # Auto-create new rivalry from match result
            if match.winner_id and len(match.participant_ids) == 2:
                loser_id = next(
                    pid for pid in match.participant_ids if pid != match.winner_id
                )
                self.rivalry_engine.maybe_create_rivalry_from_match(
                    match.winner_id, loser_id, self.state
                )

        # Show rating (weighted by importance)
        show.rating = self._compute_show_rating(show)

        # Economy
        econ_result = self.economy_engine.process_show(show, self.state)

        # ✅ FIX #2: لو الـbudget بقى موجب → نصفّر عدّاد الإفلاس
        if self.state.player_budget >= 0 and self.state.negative_weeks > 0:
            self.state.clear_bankruptcy_counter()

        # Store show in history
        self.state.shows.append(show)
        story_news = self.story_engine.advance_stories(self.state)
        for n in story_news:
            self.state.add_news(n)
        return {
            "matches": match_results,
            "show_rating": show.rating,
            "economy": econ_result,
        }

    def _compute_show_rating(self, show: Show) -> int:
        """
        Weighted average of match ratings, with main event weighted heavier.
        """
        if not show.matches:
            return 0

        total_weight = 0.0
        total_score = 0.0

        for m in show.matches:
            if m.importance == MatchImportance.MAIN_EVENT:
                w = 0.35
            elif m.importance == MatchImportance.UPPER_CARD:
                w = 0.25
            elif m.importance == MatchImportance.MIDCARD:
                w = 0.20
            else:
                w = 0.15

            total_weight += w
            total_score += m.rating * w

        if total_weight == 0:
            return 0

        rating = total_score / total_weight

        # Main event bonus
        if show.matches:
            main = next(
                (m for m in show.matches if m.importance == MatchImportance.MAIN_EVENT),
                None,
            )
            if main and main.rating >= 80:
                rating += 3

        return max(0, min(100, int(rating)))

    # =========================================================
    # AI TURN
    # =========================================================

    def run_ai_turn(self) -> dict:
        """AI books and simulates its own show."""
        ai_show = self.ai_engine.book_ai_show(self.state)
        rating = self.ai_engine.simulate_ai_show(ai_show, self.state, self.match_engine)
        econ = self.economy_engine.process_ai_week(self.state)
        return {
            "ai_show_rating": rating,
            "ai_economy": econ,
        }

    # =========================================================
    # WEEK END
    # =========================================================

    def end_week(self) -> dict:
        """
        Called after the show + AI turn.
        - tick championships
        - tick rivalries (decay / end)
        - tick injuries
        - contract weeks
        - generate random event for NEXT week
        - ✅ FIX #2: process loan payment + bankruptcy check
        """
        state = self.state

        # ----- Championships -----
        for c in state.championships:
            if c.champion_id:
                c.tick_week()

        # ----- Rivalries -----
        rivalry_news = self.rivalry_engine.weekly_update(state)

        # ----- Injuries -----
        for w in state.roster:
            if w.is_injured:
                w.injury_weeks -= 1
                if w.injury_weeks <= 0:
                    w.is_injured = False
                    w.injury_weeks = 0
                    state.add_news(f"✅ {w.name} has recovered from injury.")

        # ----- Contracts -----
        for w in state.roster:
            if w.contract_weeks > 0:
                w.contract_weeks -= 1

        # ----- Stamina recovery -----
        for w in state.roster:
            w.adjust_stamina(Config.STAMINA_RECOVERY)

        # ✅ FIX #2: قسط القرض الأسبوعي
        loan_result = self.economy_engine.process_loan_payment(state)
        if loan_result:
            state.add_news(
                f"💸 Loan payment: ${loan_result['payment']:,} "
                f"({loan_result['weeks_remaining']} weeks remaining)"
            )

        # ✅ FIX #2: تحديث عدّاد الإفلاس بعد كل التعديلات
        if state.player_budget < 0:
            state.negative_weeks += 1
            state.add_news(
                f"⚠️ Budget is negative! Week {state.negative_weeks}/"
                f"{Config.BANKRUPTCY_WEEKS} before bankruptcy."
            )
        else:
            state.negative_weeks = 0

        # ----- Generate random event for next week -----
        event = self.event_engine.generate(state)
        self.story_engine.try_create_story(state)

        # ----- Advance week -----
        state.current_week += 1

        return {
            "rivalry_news": rivalry_news,
            "event": event,
            "new_week": state.current_week,
            "loan": loan_result,
            "is_bankrupt": state.is_bankrupt(),
            "negative_weeks": state.negative_weeks,
        }

    # =========================================================
    # SEASON END
    # =========================================================

    def is_season_over(self) -> bool:
        return self.state.current_week > self.state.season_length

    def season_summary(self) -> dict:
        """Generate the end-of-season report."""
        state = self.state

        top = max(state.roster, key=lambda w: w.overall()) if state.roster else None

        best_rivalry = None
        if state.rivalries:
            best_rivalry = max(state.rivalries, key=lambda r: r.heat)

        best_rivalry_desc = "—"
        if best_rivalry:
            a = state.get_wrestler(best_rivalry.wrestler_a_id)
            b = state.get_wrestler(best_rivalry.wrestler_b_id)
            if a and b:
                best_rivalry_desc = f"{a.name} vs {b.name}"

        if state.shows:
            avg_rating = sum(s.rating for s in state.shows) // len(state.shows)
        else:
            avg_rating = 0

        profit = state.total_revenue - state.total_expenses

        return {
            "final_week": state.season_length,
            "player_fans": state.player_fans,
            "player_budget": state.player_budget,
            "total_revenue": state.total_revenue,
            "total_expenses": state.total_expenses,
            "profit": profit,
            "avg_show_rating": avg_rating,
            "best_match_rating": state.best_match_rating,
            "best_match_desc": state.best_match_desc,
            "top_superstar": top.name if top else "—",
            "best_rivalry": best_rivalry_desc,
            "shows_count": len(state.shows),
        }
