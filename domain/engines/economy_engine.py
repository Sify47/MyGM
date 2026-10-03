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

        ✅ FIX #2:
        - PLE multiplier على الإيرادات والمصاريف
        - Ticket price أعلى
        - Sponsorship أعلى
        - Bankruptcy tracking
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
        merch_revenue = int(
            actual * self.rng.uniform(Config.MERCH_MIN, Config.MERCH_MAX)
        )
        sponsorship = self._sponsorship_income(state)
        revenue = ticket_revenue + merch_revenue + sponsorship

        # ===== Expenses =====
        arena_cost = Config.ARENA_COST
        production_cost = Config.PRODUCTION_COST
        salaries = sum(w.salary for w in state.roster if w.contract_weeks > 0)
        expenses = arena_cost + production_cost + salaries

        # ✅ FIX #2: PLE multiplier
        if getattr(show, "is_ple", False):
            revenue = int(revenue * Config.PLE_REVENUE_MULT)
            expenses = int(expenses * Config.PLE_EXPENSE_MULT)

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
            "negative_weeks": getattr(state, "negative_weeks", 0),
            "is_bankrupt": (
                getattr(state, "negative_weeks", 0) >= Config.BANKRUPTCY_WEEKS
            ),
        }

    # =========================================================
    # DEMAND / PRICING
    # =========================================================

    def _compute_demand(self, show: Show, state: GameState) -> float:
        """
        Demand is a 0..1 multiplier on arena capacity.
        Based on fans, show rating expectation, star power.
        """
        fans_factor = min(1.0, state.player_fans / 200_000)

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

        momentum = 0.5
        if state.shows:
            last = state.shows[-1]
            momentum = last.rating / 100

        demand = fans_factor * 0.5 + star_power * 0.3 + momentum * 0.2
        return max(0.2, min(1.0, demand))

    def _arena_capacity(self, state: GameState) -> int:
        return 15_000

    def _ticket_price(self, state: GameState) -> int:
        # ✅ FIX #2: من Config
        return Config.TICKET_PRICE

    def _sponsorship_income(self, state: GameState) -> int:
        # ✅ FIX #2: rate من Config
        return int(state.player_fans * Config.SPONSORSHIP_RATE)

    # =========================================================
    # LOAN SYSTEM
    # =========================================================

    def take_loan(self, state: GameState) -> dict:
        """
        ✅ FIX #2: Player ياخد قرض لما الـbudget يبقى سالب.
        """
        if state.player_budget >= 0:
            return {"ok": False, "reason": "Budget is not negative."}

        if getattr(state, "active_loan", None):
            return {"ok": False, "reason": "You already have an active loan."}

        amount = Config.LOAN_AMOUNT
        total_due = int(amount * (1 + Config.LOAN_INTEREST))
        weekly_payment = total_due // Config.LOAN_REPAY_WEEKS

        state.player_budget += amount
        state.active_loan = {
            "amount": amount,
            "total_due": total_due,
            "weekly_payment": weekly_payment,
            "weeks_remaining": Config.LOAN_REPAY_WEEKS,
        }

        return {
            "ok": True,
            "amount": amount,
            "total_due": total_due,
            "weekly_payment": weekly_payment,
            "weeks_remaining": Config.LOAN_REPAY_WEEKS,
        }

    def process_loan_payment(self, state: GameState) -> dict | None:
        """
        ✅ FIX #2: يخصم القسط الأسبوعي من الـbudget.
        """
        loan = getattr(state, "active_loan", None)
        if not loan:
            return None

        payment = loan["weekly_payment"]
        state.player_budget -= payment
        loan["weeks_remaining"] -= 1

        if loan["weeks_remaining"] <= 0:
            state.active_loan = None

        return {
            "payment": payment,
            "weeks_remaining": loan["weeks_remaining"] if state.active_loan else 0,
        }

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
            delta = int(state.player_fans * 0.06)
        elif show.rating >= 60:
            delta = int(state.player_fans * 0.02)
        elif show.rating >= 40:
            delta = 0
        else:
            delta = -int(state.player_fans * 0.03)

        if profit > 0:
            delta += int(state.player_fans * 0.01)
        else:
            delta -= int(state.player_fans * 0.01)

        state.player_fans = max(1000, state.player_fans + delta)

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
