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
        self.ensure_week_setup()

    def ensure_week_setup(self) -> None:
        """Backfill weekly gameplay data for new and legacy saves."""
        if self.state.weekly_objective is None:
            self.state.weekly_objective = self.event_engine.generate_objective(
                self.state
            )
        if (
            self.state.pending_decision is None
            and self.state.decision_resolved_week != self.state.current_week
        ):
            self.state.pending_decision = self.event_engine.generate_decision(
                self.state
            )

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
        - resolve featured story arcs
        """
        match_results = []
        segment_results, segment_story_ids = self._resolve_segments(show)
        featured_story_ids = set(segment_story_ids)
        for match in show.matches:
            result = self.match_engine.simulate(match, self.state)
            match_results.append(result)

            if match.story_id:
                featured_story_ids.add(match.story_id)

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

        # Show rating (weighted by importance + rundown flow)
        show.rating = max(
            0, min(100, self._compute_show_rating(show) + self._rundown_bonus(show))
        )

        # Economy
        econ_result = self.economy_engine.process_show(show, self.state)

        # Store show in history
        self.state.shows.append(show)
        story_news = self.story_engine.advance_stories(self.state)
        for n in story_news:
            self.state.add_news(n)

        # Manual stories do not auto-advance stages, but featuring them still
        # rewards the player with heat and visible feedback.
        for story_id in featured_story_ids:
            story = self.state.get_storyline(story_id)
            if story and story.manual_mode:
                story.adjust_heat(10)

        story_updates = []
        for story_id in featured_story_ids:
            story = self.state.get_storyline(story_id)
            if not story:
                continue
            story_updates.append(
                {
                    "story_id": story.id,
                    "title": story.title,
                    "stage": story.current_stage_name,
                    "stage_number": min(story.stage + 1, story.total_stages),
                    "total_stages": story.total_stages,
                    "heat": story.heat,
                    "completed": story.completed,
                    "manual_mode": story.manual_mode,
                    "message": (
                        f"{story.title} was featured; heat is now {story.heat}."
                        if story.manual_mode
                        else (
                            f"{story.title} advanced to {story.current_stage_name}."
                            if not story.completed
                            else f"{story.title} reached its finale."
                        )
                    ),
                }
            )
        return {
            "matches": match_results,
            "show_rating": show.rating,
            "economy": econ_result,
            "segments": segment_results,
            "story_updates": story_updates,
        }

    def _resolve_segments(self, show: Show) -> tuple[list[dict], set[str]]:
        """Apply non-match moments and return readable results for the UI."""
        show.rebuild_rundown()
        results = []
        story_ids: set[str] = set()
        effects = {
            "PROMO": (2, 0, 8, "cut a promo"),
            "CALLOUT": (1, -2, 12, "delivered a heated callout"),
            "BACKSTAGE_ATTACK": (-1, -5, 15, "sparked a backstage attack"),
            "INTERFERENCE": (1, -3, 10, "caused an interference"),
            "CONTRACT_SIGNING": (1, 2, 10, "signed a contract"),
            "CELEBRATION": (3, 3, 5, "celebrated with the crowd"),
        }
        beat_types = {
            "PROMO": "PROMO",
            "CALLOUT": "CALLOUT",
            "BACKSTAGE_ATTACK": "ATTACK",
            "INTERFERENCE": "INTERFERENCE",
            "CONTRACT_SIGNING": "CONFRONTATION",
            "CELEBRATION": "RETURN",
        }
        for segment in getattr(show, "segments", []):
            segment_type = segment.get("type", "PROMO")
            pop_delta, morale_delta, heat_delta, verb = effects.get(
                segment_type, effects["PROMO"]
            )
            participants = [
                self.state.get_wrestler(pid)
                for pid in segment.get("participant_ids", [])
            ]
            participants = [w for w in participants if w]
            if not participants:
                continue
            lead = participants[0]
            lead.adjust_popularity(pop_delta)
            lead.adjust_morale(morale_delta)
            if segment_type == "BACKSTAGE_ATTACK" and len(participants) > 1:
                participants[1].adjust_health(-3)
                participants[1].adjust_morale(-4)
            if segment_type == "INTERFERENCE" and len(participants) > 1:
                participants[1].adjust_popularity(-2)

            story_id = segment.get("story_id")
            story = self.state.get_storyline(story_id) if story_id else None
            completed_beat = None
            if story:
                story_ids.add(story.id)
                position = int(segment.get("position", 0))
                adjacent_story_ids = set()
                if position > 0 and position - 1 < len(show.matches):
                    adjacent_story_ids.add(show.matches[position - 1].story_id)
                if position < len(show.matches):
                    adjacent_story_ids.add(show.matches[position].story_id)
                if story.id in adjacent_story_ids:
                    heat_delta += 5
                story.adjust_heat(heat_delta)
                desired_beat_type = beat_types.get(segment_type)
                for beat in story.get_pending_beats():
                    if (
                        desired_beat_type
                        and beat.beat_type.value == desired_beat_type
                        and set(beat.participant_ids).intersection(
                            segment.get("participant_ids", [])
                        )
                    ):
                        story.complete_beat(beat.id, self.state.current_week)
                        completed_beat = beat.label
                        break
            names = " + ".join(w.name for w in participants)
            text = f"{names} {verb}."
            results.append(
                {
                    "type": segment_type,
                    "text": text,
                    "story_id": story.id if story else None,
                    "story_title": story.title if story else None,
                    "heat_delta": heat_delta if story else 0,
                    "beat_completed": completed_beat,
                }
            )
            self.state.add_news(f"🎙️ {text}")
        return results, story_ids

    def _rundown_bonus(self, show: Show) -> int:
        """Reward a coherent opening, transitions, and a true main event."""
        show.rebuild_rundown()
        bonus = 0
        if show.rundown and show.rundown[0]["kind"] == "segment":
            first = show.segments[show.rundown[0]["index"]]
            if first.get("type") in {"PROMO", "CALLOUT"}:
                bonus += 2
        if show.rundown and show.rundown[-1]["kind"] == "match":
            last_match = show.matches[show.rundown[-1]["index"]]
            if last_match.importance == MatchImportance.MAIN_EVENT:
                bonus += 3
        for item in show.rundown:
            if item["kind"] != "segment":
                continue
            segment = show.segments[item["index"]]
            if segment.get("type") == "BACKSTAGE_ATTACK":
                bonus += 2
        return min(8, bonus)

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

        objective_result = self.event_engine.evaluate_objective(state)

        # ----- Advance week -----
        state.current_week += 1
        state.weekly_objective = self.event_engine.generate_objective(state)
        state.pending_decision = self.event_engine.generate_decision(state)
        state.decision_resolved_week = None

        return {
            "rivalry_news": rivalry_news,
            "event": event,
            "new_week": state.current_week,
            "loan": loan_result,
            "is_bankrupt": state.is_bankrupt(),
            "negative_weeks": state.negative_weeks,
            "objective": objective_result,
            "next_objective": state.weekly_objective,
            "next_decision": state.pending_decision,
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
