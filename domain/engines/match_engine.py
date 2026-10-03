"""
Match Engine - the core simulation.
Computes match rating, winner, crowd reaction, and side effects.
"""

from __future__ import annotations

import random

from config import Config
from core.enums import (
    MatchType,
    MatchImportance,
    CrowdReaction,
    WrestlerClass,
    Gender,
)
from core.constants import (
    clamp,
    get_chemistry,
    crowd_reaction_from_rating,
    stars_from_rating,
)
from domain.models.match import Match
from domain.models.wrestler import Wrestler
from domain.models.rivalry import Rivalry
from domain.models.game_state import GameState


class MatchEngineError(Exception):
    """Raised when a match cannot be simulated."""

    pass


class MatchEngine:
    """
    Stateless engine. Takes a GameState + a Match, mutates the Match
    with results, and returns a summary dict.
    """

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    # =========================================================
    # MAIN ENTRY
    # =========================================================

    def simulate(self, match: Match, state: GameState) -> dict:
        participants = [state.get_wrestler(pid) for pid in match.participant_ids]
        participants = [p for p in participants if p is not None]

        if len(participants) < 2:
            return {"error": "Not enough participants"}

        # ----- Gender validation -----
        gender_error = self._validate_genders(participants)
        if gender_error:
            return {"error": gender_error}

        # ----- Compute rating components -----
        skill_score = self._skill_score(participants)
        pop_score = self._popularity_score(participants)
        story_score = self._story_score(match, state)
        chem_score = self._chemistry_score(participants)
        importance_score = self._importance_score(match.importance)
        crowd_score = self._crowd_score(match, state)

        random_factor = self.rng.randint(Config.RANDOM_MIN, Config.RANDOM_MAX)

        raw_rating = (
            skill_score * Config.WEIGHT_SKILL
            + pop_score * Config.WEIGHT_POPULARITY
            + story_score * Config.WEIGHT_STORY
            + chem_score * Config.WEIGHT_CHEMISTRY
            + importance_score * Config.WEIGHT_IMPORTANCE
            + crowd_score * Config.WEIGHT_CROWD
        )

        final_rating = int(clamp(round(raw_rating + random_factor), 0, 100))

        # ----- Decide winner (respect override) -----
        winner = self._pick_winner(participants, match, state)

        # ----- Fill match results -----
        match.winner_id = winner.id
        match.rating = final_rating
        match.crowd_reaction = crowd_reaction_from_rating(final_rating)

        # ----- Apply side effects -----
        self._apply_side_effects(match, participants, winner, state)

        # ----- Track best match of the season -----
        if final_rating > state.best_match_rating:
            state.best_match_rating = final_rating
            names = " vs ".join(p.name for p in participants)
            state.best_match_desc = f"{names} (W{state.current_week})"

        return {
            "match_id": match.id,
            "winner_id": winner.id,
            "winner_name": winner.name,
            "rating": final_rating,
            "stars": stars_from_rating(final_rating),
            "crowd": match.crowd_reaction.value,
            "was_override": match.winner_override_id is not None,
            "components": {
                "skill": round(skill_score, 1),
                "popularity": round(pop_score, 1),
                "story": round(story_score, 1),
                "chemistry": round(chem_score, 1),
                "importance": round(importance_score, 1),
                "crowd": round(crowd_score, 1),
                "random": random_factor,
            },
        }

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_genders(self, participants: list[Wrestler]) -> str | None:
        """
        Returns error message if participants have mixed genders,
        or None if all good.
        """
        genders = {p.gender for p in participants}
        if len(genders) > 1:
            names = ", ".join(f"{p.name} ({p.gender.value})" for p in participants)
            return f"Mixed gender match not allowed: {names}"
        return None

    # =========================================================
    # RATING COMPONENTS
    # =========================================================

    def _skill_score(self, participants: list[Wrestler]) -> float:
        total = 0.0
        for p in participants:
            stamina_mod = 0.7 + (p.stamina / 100) * 0.3
            total += p.ring_skill * stamina_mod
        return total / len(participants)

    def _popularity_score(self, participants: list[Wrestler]) -> float:
        avg_pop = sum(p.popularity for p in participants) / len(participants)
        return avg_pop * 0.9 + 10

    def _story_score(self, match: Match, state: GameState) -> float:
        base = 40.0
        if match.rivalry_id:
            rivalry = state.get_rivalry(match.rivalry_id)
            if rivalry:
                base += rivalry.heat * 0.4
        if match.story_id:
            base += 15
        return clamp(base, 0, 100)

    def _chemistry_score(self, participants: list[Wrestler]) -> float:
        if len(participants) < 2:
            return 50.0

        total = 0.0
        pairs = 0
        for i in range(len(participants)):
            for j in range(i + 1, len(participants)):
                a = participants[i]
                b = participants[j]
                chem = get_chemistry(a.wrestler_class.value, b.wrestler_class.value)
                if {a.alignment.value, b.alignment.value} == {"FACE", "HEEL"}:
                    chem += 0.05
                total += chem
                pairs += 1

        avg = total / pairs if pairs else 0.85
        return clamp(avg * 100, 0, 100)

    def _importance_score(self, importance: MatchImportance) -> float:
        mapping = {
            MatchImportance.OPENER: 40,
            MatchImportance.MIDCARD: 55,
            MatchImportance.UPPER_CARD: 70,
            MatchImportance.MAIN_EVENT: 85,
        }
        return mapping.get(importance, 50)

    def _crowd_score(self, match: Match, state: GameState) -> float:
        base = 40.0
        if match.championship_id:
            base += 15
        if match.rivalry_id:
            rivalry = state.get_rivalry(match.rivalry_id)
            if rivalry:
                base += rivalry.heat * 0.3
        if match.importance == MatchImportance.MAIN_EVENT:
            base += 10
        return clamp(base, 0, 100)

    # =========================================================
    # WINNER SELECTION
    # =========================================================

    def _pick_winner(
        self,
        participants: list[Wrestler],
        match: Match,
        state: GameState,
    ) -> Wrestler:
        # ----- Winner override -----
        if match.winner_override_id:
            for p in participants:
                if p.id == match.winner_override_id:
                    return p
            # Override ID doesn't match any participant → fall through

        # ----- Weighted random pick -----
        weights = []
        for p in participants:
            score = p.popularity * 0.5 + p.ring_skill * 0.3 + p.morale * 0.2
            if p.alignment.value == "HEEL":
                score *= 1.05
            score += self.rng.uniform(-15, 15)
            weights.append(max(1.0, score))

        total = sum(weights)
        r = self.rng.uniform(0, total)
        upto = 0.0
        for p, w in zip(participants, weights):
            upto += w
            if upto >= r:
                return p
        return participants[-1]

    # =========================================================
    # SIDE EFFECTS
    # =========================================================

    def _apply_side_effects(
        self,
        match: Match,
        participants: list[Wrestler],
        winner: Wrestler,
        state: GameState,
    ) -> None:
        is_main = match.importance == MatchImportance.MAIN_EVENT
        is_title = match.championship_id is not None

        for p in participants:
            # ===== Popularity =====
            if p.id == winner.id:
                delta = Config.POP_WIN
                if is_title:
                    delta += Config.POP_CHAMPIONSHIP_WIN
                if match.rating >= 80:
                    delta += Config.POP_GREAT_MATCH
                p.adjust_popularity(delta)
                p.wins += 1
            else:
                delta = Config.POP_LOSS
                if match.rating >= 80:
                    delta += 1
                if match.rating < 40:
                    delta += Config.POP_BAD_MATCH
                p.adjust_popularity(delta)
                p.losses += 1

            # ===== Morale =====
            if p.id == winner.id:
                p.adjust_morale(Config.MORALE_WIN)
            else:
                p.adjust_morale(Config.MORALE_LOSS)
            if is_main:
                p.adjust_morale(Config.MORALE_MAIN_EVENT)

            # ===== Health =====
            health_delta = (
                Config.HEALTH_MAIN_EVENT if is_main else Config.HEALTH_NORMAL_MATCH
            )
            p.adjust_health(health_delta)

            # ===== Stamina =====
            stam_delta = Config.STAMINA_MAIN_EVENT if is_main else Config.STAMINA_MATCH
            p.adjust_stamina(stam_delta)

        # ===== Championship change =====
        if is_title and match.championship_id:
            champ = state.get_championship(match.championship_id)
            if champ:
                if champ.champion_id != winner.id:
                    # New champion
                    if champ.champion_id:
                        old = state.get_wrestler(champ.champion_id)
                        if old:
                            old.is_champion = False
                            old.championship_id = None
                    champ.change_champion(winner.id, state.current_week)
                    winner.is_champion = True
                    winner.championship_id = champ.id
                    state.add_news(f"🏆 {winner.name} wins the {champ.name}!")
                else:
                    # Successful defense
                    champ.record_defense()
                    state.add_news(f"🛡️ {winner.name} retains the {champ.name}.")
