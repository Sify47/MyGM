"""
Booking Manager - handles card building and validation.
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
)
from domain.models.match import Match
from domain.models.show import Show
from domain.models.game_state import GameState


class BookingError(Exception):
    """Raised when a booking action is invalid."""

    pass


class BookingManager:
    def __init__(self, state: GameState):
        self.state = state

    # =========================================================
    # SHOW CREATION
    # =========================================================

    def create_show(self, name: str | None = None) -> Show:
        is_ple = self.state.is_ple_week()
        if name is None:
            name = (
                f"Week {self.state.current_week} PLE"
                if is_ple
                else f"Week {self.state.current_week} Show"
            )
        return Show(
            week=self.state.current_week,
            name=name,
            is_ple=is_ple,
        )

    # =========================================================
    # MATCH CREATION
    # =========================================================

    def add_match(
        self,
        show: Show,
        match_type: MatchType,
        participant_ids: list[str],
        importance: MatchImportance = MatchImportance.MIDCARD,
        championship_id: Optional[str] = None,
        rivalry_id: Optional[str] = None,
        story_id: Optional[str] = None,
        stipulation: MatchStipulation = MatchStipulation.NORMAL,
        winner_mode: WinnerMode = WinnerMode.AUTO,
        winner_override_id: Optional[str] = None,
    ) -> Match:
        """Validate + add a match to the show."""
        self._validate_match(
            show=show,
            match_type=match_type,
            participant_ids=participant_ids,
            championship_id=championship_id,
        )

        # Validate winner_override_id if provided
        if winner_override_id and winner_override_id not in participant_ids:
            raise BookingError("Winner override must be one of the participants.")

        match = Match(
            match_type=match_type,
            participant_ids=participant_ids,
            importance=importance,
            championship_id=championship_id,
            rivalry_id=rivalry_id,
            story_id=story_id,
            stipulation=stipulation,
            winner_mode=winner_mode,
            winner_override_id=winner_override_id,
        )
        show.matches.append(match)
        return match

    def remove_match(self, show: Show, match_id: str) -> bool:
        before = len(show.matches)
        show.matches = [m for m in show.matches if m.id != match_id]
        return len(show.matches) < before

    def add_promo(
        self,
        show: Show,
        participant_id: str,
        promo_type: str = "promo",
        story_id: Optional[str] = None,
    ) -> None:
        show.promos.append(
            {
                "participant_id": participant_id,
                "type": promo_type,
                "story_id": story_id,
            }
        )

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_match(
        self,
        show: Show,
        match_type: MatchType,
        participant_ids: list[str],
        championship_id: Optional[str],
    ) -> None:
        # ----- Roster size per match type -----
        required = {
            MatchType.SINGLES: 2,
            MatchType.CHAMPIONSHIP: 2,
            MatchType.TAG_TEAM: 4,
            MatchType.TRIPLE_THREAT: 3,
            MatchType.FATAL_4_WAY: 4,
        }
        need = required.get(match_type, 2)
        if len(participant_ids) != need:
            raise BookingError(
                f"{match_type.value} needs exactly {need} participants, "
                f"got {len(participant_ids)}."
            )

        # ----- Show limit -----
        max_matches = Config.MATCHES_PER_PLE if show.is_ple else Config.MATCHES_PER_SHOW
        if len(show.matches) >= max_matches:
            raise BookingError(f"Show already has {max_matches} matches (max).")

        # ----- Every participant must exist, be available, and not booked twice -----
        already_booked = set()
        for m in show.matches:
            already_booked.update(m.participant_ids)

        participants = []
        for pid in participant_ids:
            w = self.state.get_wrestler(pid)
            if w is None:
                raise BookingError(f"Wrestler {pid} not found.")
            if not w.is_available():
                raise BookingError(
                    f"{w.name} is not available (injured or low health)."
                )
            if pid in already_booked:
                raise BookingError(f"{w.name} is already booked on this show.")
            participants.append(w)

        # ----- Gender validation -----
        self._validate_genders(participants)

        # ----- Championship validation -----
        if championship_id:
            self._validate_championship(championship_id, participants, match_type)

    def _validate_genders(self, participants: list) -> None:
        """All participants must be the same gender."""
        genders = {p.gender for p in participants}
        if len(genders) > 1:
            names = ", ".join(f"{p.name} ({p.gender.value})" for p in participants)
            raise BookingError(f"Mixed-gender matches are not allowed: {names}")

    def _validate_championship(
        self,
        championship_id: str,
        participants: list,
        match_type: MatchType,
    ) -> None:
        champ = self.state.get_championship(championship_id)
        if champ is None:
            raise BookingError("Championship not found.")

        # Champion must be in the match
        if champ.champion_id and champ.champion_id not in [p.id for p in participants]:
            raise BookingError("Championship match must include the current champion.")

        # All participants must be eligible for the championship's division
        for p in participants:
            if not champ.can_compete(p):
                raise BookingError(
                    f"{p.name} is not eligible for {champ.name} "
                    f"({champ.division.value} division)."
                )

        # Tag title needs even number of participants
        if champ.division == Division.TAG and len(participants) % 2 != 0:
            raise BookingError(
                "Tag championship match needs an even number of wrestlers."
            )

    # =========================================================
    # AUTO-COMPLETE
    # =========================================================

    def suggest_main_event(
        self,
        show: Show,
    ) -> Optional[tuple[str, str]]:
        """
        Suggest a main event based on popularity + rivalry heat.
        Respects gender matching.
        """
        available = self.state.get_available_wrestlers()
        if len(available) < 2:
            return None

        already_booked = set()
        for m in show.matches:
            already_booked.update(m.participant_ids)
        pool = [w for w in available if w.id not in already_booked]
        if len(pool) < 2:
            return None

        # Try to use an active heated rivalry
        best_rivalry = None
        best_heat = 0
        for r in self.state.get_active_rivalries():
            a = self.state.get_wrestler(r.wrestler_a_id)
            b = self.state.get_wrestler(r.wrestler_b_id)
            if not a or not b:
                continue
            if a.id in already_booked or b.id in already_booked:
                continue
            if not a.is_available() or not b.is_available():
                continue
            # Gender match
            if a.gender != b.gender:
                continue
            if r.heat > best_heat:
                best_heat = r.heat
                best_rivalry = r

        if best_rivalry and best_heat >= 40:
            return (
                best_rivalry.wrestler_a_id,
                best_rivalry.wrestler_b_id,
            )

        # Fallback: two most popular of same gender
        for gender in ("MALE", "FEMALE"):
            same = [w for w in pool if w.gender.value == gender]
            if len(same) >= 2:
                same.sort(key=lambda w: w.popularity, reverse=True)
                return (same[0].id, same[1].id)

        return None
