"""
GameState - the single source of truth for the entire game.
"""

from __future__ import annotations

from typing import Optional

from config import Config
from core.enums import Gender, Division
from domain.models.wrestler import Wrestler
from domain.models.show import Show
from domain.models.rivalry import Rivalry
from domain.models.storyline import Storyline
from domain.models.championship import Championship
from data.seed_ai_wrestlers import seed_ai_roster


class GameState:
    def __init__(self):
        # ===== Time =====
        self.current_week: int = 1
        self.season_length: int = Config.SEASON_LENGTH_WEEKS

        # ===== Player Promotion =====
        self.player_name: str = "My Promotion"
        self.player_budget: int = Config.STARTING_BUDGET
        self.player_fans: int = Config.STARTING_FANS
        self.player_casual_fans: int = int(Config.STARTING_FANS * Config.CASUAL_RATIO)
        self.player_hardcore_fans: int = int(
            Config.STARTING_FANS * (1 - Config.CASUAL_RATIO)
        )

        # ===== AI Promotion =====
        self.ai_name: str = "Rival Promotion"
        self.ai_budget: int = Config.STARTING_BUDGET
        self.ai_fans: int = Config.STARTING_FANS
        self.ai_last_show_rating: int = 50
        self.ai_roster: list[Wrestler] = []

        # ===== Player Roster (unified list) =====
        self.roster: list[Wrestler] = []

        # ===== Championships =====
        self.championships: list[Championship] = []

        # ===== Active Rivalries =====
        self.rivalries: list[Rivalry] = []

        # ===== Active Storylines =====
        self.storylines: list[Storyline] = []

        # ===== Shows (history) =====
        self.shows: list[Show] = []

        # ===== News Feed =====
        self.news: list[dict] = []

        # ===== Weekly gameplay layer =====
        self.weekly_objective: Optional[dict] = None
        self.pending_decision: Optional[dict] = None
        self.decision_resolved_week: Optional[int] = None
        self.last_objective_result: Optional[dict] = None
        self.last_decision_result: Optional[dict] = None

        # ===== Season Stats =====
        self.total_revenue: int = 0
        self.total_expenses: int = 0
        self.best_match_rating: int = 0
        self.best_match_desc: str = ""

        # ===== Bankruptcy + Loan tracking  (✅ FIX #2) =====
        self.negative_weeks: int = 0
        self.active_loan: Optional[dict] = None

    # =========================================================
    # ROSTER HELPERS
    # =========================================================

    def get_wrestler(self, wrestler_id: str) -> Optional[Wrestler]:
        for w in self.roster:
            if w.id == wrestler_id:
                return w
        for w in self.ai_roster:
            if w.id == wrestler_id:
                return w
        return None

    def get_available_wrestlers(self) -> list[Wrestler]:
        return [w for w in self.roster if w.is_available()]

    # ===== Gender-Based Getters =====

    @property
    def roster_male(self) -> list[Wrestler]:
        return [w for w in self.roster if w.gender == Gender.MALE]

    @property
    def roster_female(self) -> list[Wrestler]:
        return [w for w in self.roster if w.gender == Gender.FEMALE]

    def get_male_roster(self) -> list[Wrestler]:
        return self.roster_male

    def get_female_roster(self) -> list[Wrestler]:
        return self.roster_female

    def get_available_male(self) -> list[Wrestler]:
        return [w for w in self.roster_male if w.is_available()]

    def get_available_female(self) -> list[Wrestler]:
        return [w for w in self.roster_female if w.is_available()]

    # ===== Division-Based Getters =====

    def get_wrestlers_by_division(self, division: Division) -> list[Wrestler]:
        if division == Division.MEN:
            return self.roster_male
        if division == Division.WOMEN:
            return self.roster_female
        if division == Division.OPEN:
            return list(self.roster)
        if division == Division.TAG:
            return list(self.roster)
        return []

    def get_championships_by_division(self, division: Division) -> list[Championship]:
        return [c for c in self.championships if c.division == division]

    # =========================================================
    # CHAMPIONSHIP HELPERS
    # =========================================================

    def get_championship(self, championship_id: str) -> Optional[Championship]:
        for c in self.championships:
            if c.id == championship_id:
                return c
        return None

    def get_champion_of(self, championship_id: str) -> Optional[Wrestler]:
        c = self.get_championship(championship_id)
        if c and c.champion_id:
            return self.get_wrestler(c.champion_id)
        return None

    def get_championships_for_wrestler(self, wrestler: Wrestler) -> list[Championship]:
        """Which titles can this wrestler compete for?"""
        return [c for c in self.championships if c.can_compete(wrestler)]

    # =========================================================
    # RIVALRY HELPERS
    # =========================================================

    def get_rivalry(self, rivalry_id: str) -> Optional[Rivalry]:
        for r in self.rivalries:
            if r.id == rivalry_id:
                return r
        return None

    def find_rivalry_between(self, a_id: str, b_id: str) -> Optional[Rivalry]:
        for r in self.rivalries:
            if r.involves(a_id) and r.involves(b_id):
                return r
        return None

    def get_active_rivalries(self) -> list[Rivalry]:
        return [r for r in self.rivalries if r.is_active()]

    # =========================================================
    # STORY HELPERS
    # =========================================================

    def get_storyline(self, story_id: str) -> Optional[Storyline]:
        for s in self.storylines:
            if s.id == story_id:
                return s
        return None

    def get_active_storylines(self) -> list[Storyline]:
        return [s for s in self.storylines if s.is_active()]

    # =========================================================
    # NEWS HELPERS
    # =========================================================

    def add_news(self, text: str) -> None:
        self.news.append({"week": self.current_week, "text": text})
        if len(self.news) > 30:
            self.news = self.news[-30:]

    # =========================================================
    # ECONOMY HELPERS
    # =========================================================

    def apply_profit(self, revenue: int, expenses: int) -> int:
        profit = revenue - expenses
        self.player_budget += profit
        self.total_revenue += revenue
        self.total_expenses += expenses
        return profit

    # =========================================================
    # BANKRUPTCY / LOAN HELPERS  (✅ FIX #2)
    # =========================================================

    def is_bankrupt(self) -> bool:
        """3 أسابيع متتالية بالسالب → Game Over."""
        return self.negative_weeks >= Config.BANKRUPTCY_WEEKS

    def has_active_loan(self) -> bool:
        return self.active_loan is not None

    def clear_bankruptcy_counter(self) -> None:
        """لما الـbudget يرجع موجب."""
        self.negative_weeks = 0

    # =========================================================
    # TIME HELPERS
    # =========================================================

    def is_ple_week(self) -> bool:
        return self.current_week in Config.PLE_WEEKS

    def is_final_week(self) -> bool:
        return self.current_week >= self.season_length

    # =========================================================
    # SERIALIZATION
    # =========================================================

    def to_dict(self) -> dict:
        return {
            "current_week": self.current_week,
            "season_length": self.season_length,
            "player_name": self.player_name,
            "player_budget": self.player_budget,
            "player_fans": self.player_fans,
            "player_casual_fans": self.player_casual_fans,
            "player_hardcore_fans": self.player_hardcore_fans,
            "ai_name": self.ai_name,
            "ai_budget": self.ai_budget,
            "ai_fans": self.ai_fans,
            "ai_last_show_rating": self.ai_last_show_rating,
            "ai_roster": [w.to_dict() for w in self.ai_roster],
            "roster": [w.to_dict() for w in self.roster],
            "championships": [c.to_dict() for c in self.championships],
            "rivalries": [r.to_dict() for r in self.rivalries],
            "storylines": [s.to_dict() for s in self.storylines],
            "shows": [s.to_dict() for s in self.shows],
            "news": list(self.news),
            "weekly_objective": self.weekly_objective,
            "pending_decision": self.pending_decision,
            "decision_resolved_week": self.decision_resolved_week,
            "last_objective_result": self.last_objective_result,
            "last_decision_result": self.last_decision_result,
            "total_revenue": self.total_revenue,
            "total_expenses": self.total_expenses,
            "best_match_rating": self.best_match_rating,
            "best_match_desc": self.best_match_desc,
            # ✅ FIX #2
            "negative_weeks": self.negative_weeks,
            "active_loan": self.active_loan,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        gs = cls()
        gs.current_week = data.get("current_week", 1)
        gs.season_length = data.get("season_length", Config.SEASON_LENGTH_WEEKS)
        gs.player_name = data.get("player_name", "My Promotion")
        gs.player_budget = data.get("player_budget", Config.STARTING_BUDGET)
        gs.player_fans = data.get("player_fans", Config.STARTING_FANS)
        gs.player_casual_fans = data.get("player_casual_fans", 0)
        gs.player_hardcore_fans = data.get("player_hardcore_fans", 0)
        gs.ai_name = data.get("ai_name", "Rival Promotion")
        gs.ai_budget = data.get("ai_budget", Config.STARTING_BUDGET)
        gs.ai_fans = data.get("ai_fans", Config.STARTING_FANS)
        gs.ai_last_show_rating = data.get("ai_last_show_rating", 50)

        gs.roster = [Wrestler.from_dict(w) for w in data.get("roster", [])]
        saved_ai_roster = data.get("ai_roster")
        gs.ai_roster = (
            [Wrestler.from_dict(w) for w in saved_ai_roster]
            if saved_ai_roster is not None
            else seed_ai_roster()
        )
        gs.championships = [
            Championship.from_dict(c) for c in data.get("championships", [])
        ]
        gs.rivalries = [Rivalry.from_dict(r) for r in data.get("rivalries", [])]
        gs.storylines = [Storyline.from_dict(s) for s in data.get("storylines", [])]
        gs.shows = [Show.from_dict(s) for s in data.get("shows", [])]
        gs.news = data.get("news", [])
        gs.weekly_objective = data.get("weekly_objective")
        gs.pending_decision = data.get("pending_decision")
        gs.decision_resolved_week = data.get("decision_resolved_week")
        gs.last_objective_result = data.get("last_objective_result")
        gs.last_decision_result = data.get("last_decision_result")
        gs.total_revenue = data.get("total_revenue", 0)
        gs.total_expenses = data.get("total_expenses", 0)
        gs.best_match_rating = data.get("best_match_rating", 0)
        gs.best_match_desc = data.get("best_match_desc", "")
        # ✅ FIX #2
        gs.negative_weeks = data.get("negative_weeks", 0)
        gs.active_loan = data.get("active_loan", None)
        return gs

    def __repr__(self) -> str:
        return (
            f"<GameState W{self.current_week}/{self.season_length} "
            f"roster={len(self.roster)} "
            f"(M={len(self.roster_male)}, F={len(self.roster_female)})>"
        )
