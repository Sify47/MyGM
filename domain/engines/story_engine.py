"""
Story Engine - creates, advances, and completes auto-generated storylines.
Manual stories are handled by StoryBuilder.
"""

from __future__ import annotations

import random

from core.enums import (
    StoryType,
    Alignment,
    RivalryStage,
)
from domain.models.storyline import Storyline
from domain.models.game_state import GameState


class StoryEngine:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    # =========================================================
    # CREATE STORIES (auto)
    # =========================================================

    def try_create_story(self, state: GameState) -> Storyline | None:
        active = self.get_active_stories(state)
        if len(active) >= 3:
            return None

        if self.rng.random() > 0.40:
            return None

        candidates = self._pick_candidates(state)
        if not candidates:
            return None

        story_type, participant_ids = self.rng.choice(candidates)
        story = Storyline(
            story_type=story_type,
            participant_ids=participant_ids,
            manual_mode=False,
        )
        state.storylines.append(story)

        # Link to wrestlers
        for pid in participant_ids:
            w = state.get_wrestler(pid)
            if w:
                w.current_story_id = story.id

        # News
        a = state.get_wrestler(participant_ids[0])
        b = state.get_wrestler(participant_ids[1]) if len(participant_ids) > 1 else None
        names = a.name if a else "?"
        if b:
            names += f" & {b.name}"
        state.add_news(f"📖 New storyline: {story.title} ({names})")
        return story

    def _pick_candidates(
        self,
        state: GameState,
    ) -> list[tuple[StoryType, list[str]]]:
        candidates: list[tuple[StoryType, list[str]]] = []

        available = [
            w for w in state.roster if w.is_available() and not w.current_story_id
        ]
        if len(available) < 2:
            return candidates

        # ---- Rise of a Star ----
        rookies = [w for w in available if "Rookie" in w.traits and w.popularity < 60]
        if rookies:
            rookie = max(rookies, key=lambda w: w.potential)
            partners = [
                w
                for w in available
                if w.id != rookie.id
                and w.gender == rookie.gender
                and (w.popularity > 65 or "Veteran" in w.traits)
            ]
            if partners:
                partner = self.rng.choice(partners)
                candidates.append(
                    (
                        StoryType.RISE_OF_A_STAR,
                        [rookie.id, partner.id],
                    )
                )

        # ---- Champion vs Challenger (per division) ----
        for champ in state.championships:
            if not champ.champion_id:
                continue
            champion = state.get_wrestler(champ.champion_id)
            if not champion:
                continue
            challengers = [
                w
                for w in available
                if w.id != champion.id and w.popularity > 60 and champ.can_compete(w)
            ]
            if challengers:
                challenger = max(challengers, key=lambda w: w.popularity)
                candidates.append(
                    (
                        StoryType.CHAMPION_VS_CHALLENGER,
                        [champion.id, challenger.id],
                    )
                )

        # ---- Underdog ----
        underdogs = [w for w in available if w.popularity < 65 and w.morale > 50]
        if underdogs:
            ud = self.rng.choice(underdogs)
            big = [
                w
                for w in available
                if w.id != ud.id
                and w.gender == ud.gender
                and w.popularity > ud.popularity + 15
            ]
            if big:
                opp = self.rng.choice(big)
                candidates.append(
                    (
                        StoryType.UNDERDOG,
                        [ud.id, opp.id],
                    )
                )

        # ---- Betrayal ----
        for a in available:
            for b in available:
                if a.id >= b.id:
                    continue
                if a.gender != b.gender:
                    continue
                if a.alignment == b.alignment:
                    if self.rng.random() < 0.15:
                        candidates.append(
                            (
                                StoryType.BETRAYAL,
                                [a.id, b.id],
                            )
                        )

        # ---- Tag Team Breakup ----
        tag_specialists = [w for w in available if "Tag Specialist" in w.traits]
        # Need 2 of same gender
        for gender in ("MALE", "FEMALE"):
            same = [w for w in tag_specialists if w.gender.value == gender]
            if len(same) >= 2:
                a, b = self.rng.sample(same, 2)
                candidates.append(
                    (
                        StoryType.TAG_TEAM_BREAKUP,
                        [a.id, b.id],
                    )
                )

        return candidates

    # =========================================================
    # GETTERS
    # =========================================================

    def get_active_stories(self, state: GameState) -> list[Storyline]:
        return [s for s in state.storylines if s.is_active()]

    def get_story(
        self,
        state: GameState,
        story_id: str,
    ) -> Storyline | None:
        for s in state.storylines:
            if s.id == story_id:
                return s
        return None

    # =========================================================
    # ADVANCE (only auto stories)
    # =========================================================

    def advance_stories(self, state: GameState) -> list[str]:
        """
        Only advances auto stories (manual_mode=False).
        Manual stories are advanced by the player.
        """
        news = []
        last_show = state.shows[-1] if state.shows else None
        if not last_show:
            return news

        featured_ids = set()
        for m in last_show.matches:
            if m.story_id:
                featured_ids.add(m.story_id)
        for p in last_show.promos:
            sid = p.get("story_id")
            if sid:
                featured_ids.add(sid)

        for story in self.get_active_stories(state):
            # Skip manual stories
            if story.manual_mode:
                continue

            story.weeks_active += 1

            if story.id in featured_ids:
                story.adjust_heat(+10)
                completed = story.advance_stage(
                    state.current_week, note="Featured on show"
                )
                if completed:
                    news.append(f"🎬 Storyline complete: {story.title}")
                    self._complete_story(story, state)
            else:
                story.adjust_heat(-5)
                if story.heat < 10:
                    story.completed = True
                    news.append(f"📖 Storyline fizzled out: {story.title}")
                    self._complete_story(story, state)

        return news

    def _complete_story(self, story: Storyline, state: GameState) -> None:
        for pid in story.participant_ids:
            w = state.get_wrestler(pid)
            if w and w.current_story_id == story.id:
                w.current_story_id = None

    # =========================================================
    # SUGGEST BOOKING
    # =========================================================

    def suggest_match_for_story(
        self,
        story: Storyline,
        state: GameState,
    ) -> dict:
        stage = story.current_stage_name

        suggestion = {
            "story_id": story.id,
            "match_type": "SINGLES",
            "importance": "MIDCARD",
        }

        if story.story_type == StoryType.CHAMPION_VS_CHALLENGER:
            if stage in ("Face-to-Face", "Title Match"):
                suggestion["importance"] = "MAIN_EVENT"
                suggestion["match_type"] = "CHAMPIONSHIP"

        elif story.story_type == StoryType.RISE_OF_A_STAR:
            if stage in ("Statement", "Breakthrough"):
                suggestion["importance"] = "UPPER_CARD"
            if stage == "Breakthrough":
                suggestion["importance"] = "MAIN_EVENT"

        elif story.story_type == StoryType.UNDERDOG:
            if stage in ("Shot", "Payoff"):
                suggestion["importance"] = "UPPER_CARD"
            if stage == "Payoff":
                suggestion["importance"] = "MAIN_EVENT"

        elif story.story_type == StoryType.BETRAYAL:
            if stage in ("Turn", "Revenge"):
                suggestion["importance"] = "MAIN_EVENT"

        elif story.story_type == StoryType.TAG_TEAM_BREAKUP:
            if stage == "Blowoff":
                suggestion["importance"] = "MAIN_EVENT"

        return suggestion
