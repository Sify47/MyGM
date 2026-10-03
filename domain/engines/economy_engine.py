"""
Economy Engine - handles revenue, expenses, attendance, fans.
"""

from __future__ import annotations

import random

from config import Config
from domain.models.show import Show
from domain.models.game_state import GameState


class EconomyEngine:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    # =========================================================
    # SHOW ECONOMY
    # =========================================================

    def process_show(self, show: Show, state: GameState) -> dict:
        """
        Compute attendance, revenue, expenses, and update GameState.
        Returns a summary dict.
        """
        # ===== Attendance =====
        demand = self._compute_demand(show, state)
        capacity = self._arena_capacity(state)
        expected = int(capacity * demand)
        actual = int(expected * self.rng.uniform(0.90, 1.05))
        actual = min(actual, capacity)

        # ===== Revenue =====
        ticket_price = self._ticket_price(state)
        ticket_revenue = actual * ticket_price
        merch_revenue = int(actual * self.rng.uniform(5, 12))
        sponsorship = self._sponsorship_income(state)
        revenue = ticket_revenue + merch_revenue + sponsorship

        # ===== Expenses =====
        arena_cost = Config.ARENA_COST
        production_cost = Config.PRODUCTION_COST
        salaries = sum(w.salary for w in state.roster if w.contract_weeks > 0)
        expenses = arena_cost + production_cost + salaries

        # ===== Apply =====
        profit = state.apply_profit(revenue, expenses)

        show.expected_attendance = expected
        show.actual_attendance = actual
        show.revenue = revenue
        show.expenses = expenses

        # ===== Fans change =====
        self._update_fans(show, state, profit)

        return {
            "attendance": actual,
            "capacity": capacity,
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit,
            "budget_after": state.player_budget,
        }

    # =========================================================
    # DEMAND / PRICING
    # =========================================================

    def _compute_demand(self, show: Show, state: GameState) -> float:
        """
        Demand is a 0..1 multiplier on arena capacity.
        Based on fans, show rating expectation, star power.
        """
        # Base from fans (100K fans -> 0.5 demand)
        fans_factor = min(1.0, state.player_fans / 200_000)

        # Star power of the card
        star_power = 0.5
        if show.matches:
            avg_pop = 0.0
            count = 0
            for m in show.matches:
                for pid in m.participant_ids:
                    w = state.get_wrestler(pid)
                    if w:
                        avg_pop += w.popularity
                        count += 1
            if count:
                star_power = avg_pop / count / 100

        # Previous show momentum
        momentum = 0.5
        if state.shows:
            last = state.shows[-1]
            momentum = last.rating / 100

        demand = fans_factor * 0.5 + star_power * 0.3 + momentum * 0.2
        return max(0.2, min(1.0, demand))

    def _arena_capacity(self, state: GameState) -> int:
        """
        Static arena for MVP. Later this can scale with upgrades.
        """
        return 15_000

    def _ticket_price(self, state: GameState) -> int:
        """Simple flat ticket price for MVP."""
        return 40

    def _sponsorship_income(self, state: GameState) -> int:
        """Sponsorship scales with fans."""
        return int(state.player_fans * 0.05)

    # =========================================================
    # FANS
    # =========================================================

    def _update_fans(
        self,
        show: Show,
        state: GameState,
        profit: int,
    ) -> None:
        """
        Fans grow or shrink based on show quality and profit.
        """
        delta = 0

        if show.rating >= 80:
            delta = int(state.player_fans * 0.06)  # +6%
        elif show.rating >= 60:
            delta = int(state.player_fans * 0.02)  # +2%
        elif show.rating >= 40:
            delta = 0
        else:
            delta = -int(state.player_fans * 0.03)  # -3%

        # Bonus for profit
        if profit > 0:
            delta += int(state.player_fans * 0.01)
        else:
            delta -= int(state.player_fans * 0.01)

        state.player_fans = max(1000, state.player_fans + delta)

        # Split casual/hardcore
        state.player_casual_fans = int(state.player_fans * Config.CASUAL_RATIO)
        state.player_hardcore_fans = state.player_fans - state.player_casual_fans

    # =========================================================
    # AI ECONOMY (lightweight)
    # =========================================================

    def process_ai_week(self, state: GameState) -> dict:
        """
        Simplified AI economy: gains/loses fans based on last rating.
        """
        rating = state.ai_last_show_rating
        if rating >= 75:
            delta = int(state.ai_fans * 0.05)
        elif rating >= 55:
            delta = int(state.ai_fans * 0.015)
        elif rating >= 40:
            delta = 0
        else:
            delta = -int(state.ai_fans * 0.025)

        state.ai_fans = max(1000, state.ai_fans + delta)
        state.ai_budget += self.rng.randint(-20_000, 60_000)

        return {
            "ai_fans": state.ai_fans,
            "ai_budget": state.ai_budget,
        }
