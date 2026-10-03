"""
Game Manager - the main facade the UI talks to.
"""

from __future__ import annotations

from typing import Optional

from config import Config
from core.enums import (
    MatchType,
    MatchImportance,
    MatchStipulation,
    WinnerMode,
    Division,
    ChampionshipTier,
    Gender,
)
from domain.models.game_state import GameState
from domain.models.championship import Championship
from data.seed_wrestlers import seed_roster
from data.save_manager import SaveManager
from game.booking_manager import BookingManager, BookingError
from game.turn_manager import TurnManager


class GameManager:
    def __init__(
        self,
        state: Optional[GameState] = None,
        seed: int | None = None,
    ):
        self.state = state or GameState()
        self.turn = TurnManager(self.state, seed=seed)
        self.booking = BookingManager(self.state)
        self.saves = SaveManager()

    # =========================================================
    # NEW GAME
    # =========================================================

    @classmethod
    def new_game(
        cls,
        player_name: str = "My Promotion",
        seed: int | None = None,
    ) -> "GameManager":
        state = GameState()
        state.player_name = player_name
        state.roster = seed_roster()

        # ----- Create Championships (WWE-style) -----
        world_heavyweight = Championship(
            name="World Heavyweight Championship",
            division=Division.MEN,
            tier=ChampionshipTier.TOP,
            prestige=75,
            min_popularity=70,
        )
        intercontinental = Championship(
            name="Intercontinental Championship",
            division=Division.MEN,
            tier=ChampionshipTier.MID,
            prestige=60,
            min_popularity=55,
        )
        united_states = Championship(
            name="United States Championship",
            division=Division.MEN,
            tier=ChampionshipTier.MID,
            prestige=58,
            min_popularity=50,
        )
        world_womens = Championship(
            name="World Women's Championship",
            division=Division.WOMEN,
            tier=ChampionshipTier.TOP,
            prestige=75,
            min_popularity=70,
        )
        womens_ic = Championship(
            name="Women's Intercontinental Championship",
            division=Division.WOMEN,
            tier=ChampionshipTier.MID,
            prestige=60,
            min_popularity=55,
        )
        tag_team = Championship(
            name="World Tag Team Championship",
            division=Division.TAG,
            tier=ChampionshipTier.TAG,
            prestige=65,
            min_popularity=60,
        )

        state.championships = [
            world_heavyweight,
            intercontinental,
            united_states,
            world_womens,
            womens_ic,
            tag_team,
        ]

        # ----- Assign inaugural champions -----
        males = sorted(
            state.roster_male,
            key=lambda w: w.popularity,
            reverse=True,
        )
        females = sorted(
            state.roster_female,
            key=lambda w: w.popularity,
            reverse=True,
        )

        # Men's champions
        if len(males) >= 4:
            cls._assign_champion(world_heavyweight, males[0], state)
            cls._assign_champion(intercontinental, males[1], state)
            cls._assign_champion(united_states, males[2], state)
            cls._assign_champion(tag_team, males[3], state)

        # Women's champions
        if len(females) >= 2:
            cls._assign_champion(world_womens, females[0], state)
            cls._assign_champion(womens_ic, females[1], state)

        # ----- Welcome news -----
        state.add_news(f"🎉 Welcome to {player_name}!")
        if males:
            state.add_news(
                f"🏆 {males[0].name} is your inaugural " f"World Heavyweight Champion."
            )
        if females:
            state.add_news(
                f"🏆 {females[0].name} is your inaugural " f"World Women's Champion."
            )

        return cls(state=state, seed=seed)

    @staticmethod
    def _assign_champion(
        championship: Championship,
        wrestler,
        state: GameState,
    ) -> None:
        championship.champion_id = wrestler.id
        wrestler.is_champion = True
        wrestler.championship_id = championship.id

    # =========================================================
    # LOAD
    # =========================================================

    @classmethod
    def load_game(
        cls,
        filename: str | None = None,
    ) -> Optional["GameManager"]:
        saves = SaveManager()
        state = saves.load(filename)
        if state is None:
            return None
        return cls(state=state)

    def save_game(self, filename: str | None = None) -> str:
        return self.saves.save(self.state, filename)

    # =========================================================
    # PLAYER SHOW
    # =========================================================

    def simulate_player_show(self, show) -> dict:
        return self.turn.simulate_show(show)

    def run_ai_turn(self) -> dict:
        return self.turn.run_ai_turn()

    def end_week(self) -> dict:
        return self.turn.end_week()

    def is_season_over(self) -> bool:
        return self.turn.is_season_over()

    def season_summary(self) -> dict:
        return self.turn.season_summary()

    # =========================================================
    # AUTO-BUILD (for quick testing / demo)
    # =========================================================

    def auto_build_show(self):
        """
        Build a full show automatically.
        Respects gender + supports championships.
        """
        show = self.booking.create_show()
        max_matches = Config.MATCHES_PER_PLE if show.is_ple else Config.MATCHES_PER_SHOW

        # Get available wrestlers per gender
        available_male = [
            w for w in self.state.get_available_male() if w.contract_weeks > 0
        ]
        available_female = [
            w for w in self.state.get_available_female() if w.contract_weeks > 0
        ]

        available_male.sort(key=lambda w: w.popularity, reverse=True)
        available_female.sort(key=lambda w: w.popularity, reverse=True)

        # ----- Match 1: Main Event (Men) -----
        if len(available_male) >= 2:
            top_men = available_male[:2]
            self.booking.add_match(
                show,
                match_type=MatchType.SINGLES,
                participant_ids=[top_men[0].id, top_men[1].id],
                importance=MatchImportance.MAIN_EVENT,
            )

        # ----- Match 2: Women's Championship Match -----
        if len(available_female) >= 2 and len(show.matches) < max_matches:
            womens_title = next(
                (
                    c
                    for c in self.state.championships
                    if c.division == Division.WOMEN and c.tier == ChampionshipTier.TOP
                ),
                None,
            )
            if womens_title and womens_title.champion_id:
                champion = self.state.get_wrestler(womens_title.champion_id)
                # Pick a challenger
                challengers = [
                    w
                    for w in available_female
                    if w.id != womens_title.champion_id and w.popularity >= 65
                ]
                if champion and challengers:
                    challenger = challengers[0]
                    self.booking.add_match(
                        show,
                        match_type=MatchType.CHAMPIONSHIP,
                        participant_ids=[champion.id, challenger.id],
                        importance=MatchImportance.UPPER_CARD,
                        championship_id=womens_title.id,
                    )

        # ----- Match 3: Mid-card Men's -----
        remaining_male = [
            w
            for w in available_male
            if w.id not in {pid for m in show.matches for pid in m.participant_ids}
        ]
        if len(remaining_male) >= 2 and len(show.matches) < max_matches:
            self.booking.add_match(
                show,
                match_type=MatchType.SINGLES,
                participant_ids=[remaining_male[0].id, remaining_male[1].id],
                importance=MatchImportance.MIDCARD,
            )

        # ----- Match 4: More Women's -----
        remaining_female = [
            w
            for w in available_female
            if w.id not in {pid for m in show.matches for pid in m.participant_ids}
        ]
        if len(remaining_female) >= 2 and len(show.matches) < max_matches:
            self.booking.add_match(
                show,
                match_type=MatchType.SINGLES,
                participant_ids=[remaining_female[0].id, remaining_female[1].id],
                importance=MatchImportance.MIDCARD,
            )

        # ----- Fill remaining slots -----
        while len(show.matches) < max_matches:
            # Try men first
            remaining = [
                w
                for w in available_male + available_female
                if w.id not in {pid for m in show.matches for pid in m.participant_ids}
            ]
            if len(remaining) < 2:
                break

            # Pick two of same gender
            pair = self._pick_same_gender_pair(remaining)
            if pair is None:
                break

            importance = MatchImportance.OPENER
            self.booking.add_match(
                show,
                match_type=MatchType.SINGLES,
                participant_ids=[pair[0].id, pair[1].id],
                importance=importance,
            )

        return show

    def _pick_same_gender_pair(self, pool: list):
        """Pick two wrestlers of the same gender from the pool."""
        for gender in (Gender.MALE, Gender.FEMALE):
            same = [w for w in pool if w.gender == gender]
            if len(same) >= 2:
                return (same[0], same[1])
        return None
