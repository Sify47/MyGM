"""
Story Builder - allows the player to build a story manually.
Handles:
- Creating a story with chosen type + participants
- Adding beats (from library or custom)
- Reordering / removing beats
- Advancing stages manually
"""

from __future__ import annotations

from typing import Optional

from core.enums import StoryType, StoryBeatType
from domain.models.storyline import Storyline
from domain.models.story_beat import StoryBeat
from domain.models.game_state import GameState
from data.story_beats_library import (
    get_template_by_label,
    get_suggested_beats_for_stage,
)


class StoryBuilderError(Exception):
    pass


class StoryBuilder:
    def __init__(self, state: GameState):
        self.state = state

    # =========================================================
    # CREATE STORY
    # =========================================================

    def create_story(
        self,
        story_type: StoryType,
        participant_ids: list[str],
        title: str = "",
    ) -> Storyline:
        # Validate participants
        if len(participant_ids) < 2:
            raise StoryBuilderError("A story needs at least 2 participants.")

        for pid in participant_ids:
            w = self.state.get_wrestler(pid)
            if w is None:
                raise StoryBuilderError(f"Wrestler {pid} not found.")
            if w.current_story_id:
                raise StoryBuilderError(f"{w.name} is already in a story.")

        # Gender validation for participants
        genders = {self.state.get_wrestler(pid).gender for pid in participant_ids}
        if len(genders) > 1:
            raise StoryBuilderError("All story participants must be the same gender.")

        story = Storyline(
            story_type=story_type,
            participant_ids=participant_ids,
            title=title,
            manual_mode=True,
        )
        self.state.storylines.append(story)

        # Link to wrestlers
        for pid in participant_ids:
            w = self.state.get_wrestler(pid)
            if w:
                w.current_story_id = story.id

        # News
        names = " & ".join(self.state.get_wrestler(pid).name for pid in participant_ids)
        self.state.add_news(f"📖 New storyline created: {story.title} ({names})")

        return story

    # =========================================================
    # DELETE STORY
    # =========================================================

    def delete_story(self, story_id: str) -> bool:
        story = self.state.get_storyline(story_id)
        if story is None:
            return False

        # Unlink wrestlers
        for pid in story.participant_ids:
            w = self.state.get_wrestler(pid)
            if w and w.current_story_id == story.id:
                w.current_story_id = None

        story.completed = True
        self.state.add_news(f"❌ Storyline cancelled: {story.title}")
        return True

    # =========================================================
    # BEAT MANAGEMENT
    # =========================================================

    def add_beat_from_library(
        self,
        story_id: str,
        beat_label: str,
        custom_text: str = "",
    ) -> StoryBeat:
        story = self.state.get_storyline(story_id)
        if story is None:
            raise StoryBuilderError("Story not found.")

        template = get_template_by_label(beat_label)
        if template is None:
            raise StoryBuilderError(f"Beat '{beat_label}' not found in library.")

        beat = StoryBeat(
            beat_type=template["beat_type"],
            label=template["label"],
            description=template["description"],
            participant_ids=list(story.participant_ids),
            custom_text=custom_text,
        )
        story.add_beat(beat)
        return beat

    def add_custom_beat(
        self,
        story_id: str,
        beat_type: StoryBeatType,
        label: str,
        description: str = "",
        custom_text: str = "",
    ) -> StoryBeat:
        story = self.state.get_storyline(story_id)
        if story is None:
            raise StoryBuilderError("Story not found.")

        beat = StoryBeat(
            beat_type=beat_type,
            label=label,
            description=description,
            participant_ids=list(story.participant_ids),
            custom_text=custom_text,
        )
        story.add_beat(beat)
        return beat

    def remove_beat(self, story_id: str, beat_id: str) -> bool:
        story = self.state.get_storyline(story_id)
        if story is None:
            return False

        before = len(story.beats)
        story.beats = [b for b in story.beats if b.id != beat_id]
        return len(story.beats) < before

    def complete_beat(
        self,
        story_id: str,
        beat_id: str,
        week: Optional[int] = None,
    ) -> bool:
        story = self.state.get_storyline(story_id)
        if story is None:
            return False
        week = week or self.state.current_week
        return story.complete_beat(beat_id, week)

    def advance_stage_manual(self, story_id: str) -> bool:
        """
        Force advance to next stage (manual control).
        """
        story = self.state.get_storyline(story_id)
        if story is None:
            return False
        if story.completed:
            return False
        if story.stage >= story.total_stages - 1 and not story.payoff_ready:
            self.state.add_news(
                f"⚠️ لا يمكن إنهاء قصة {story.title} قبل تنفيذ كل الـBeats."
            )
            return False

        completed = story.advance_stage(
            self.state.current_week,
            note="Manual advance",
        )
        if completed:
            # Unlink wrestlers
            for pid in story.participant_ids:
                w = self.state.get_wrestler(pid)
                if w and w.current_story_id == story.id:
                    w.current_story_id = None
            self.state.add_news(f"🎬 Storyline complete: {story.title}")
        return True

    # =========================================================
    # SUGGESTIONS
    # =========================================================

    def get_suggested_beats(self, story_id: str) -> list[str]:
        story = self.state.get_storyline(story_id)
        if story is None:
            return []
        return get_suggested_beats_for_stage(
            story.story_type.value,
            story.stage,
        )

    # =========================================================
    # ADD PARTICIPANT
    # =========================================================

    def add_participant(
        self,
        story_id: str,
        wrestler_id: str,
    ) -> bool:
        story = self.state.get_storyline(story_id)
        if story is None:
            return False

        if wrestler_id in story.participant_ids:
            return False

        w = self.state.get_wrestler(wrestler_id)
        if w is None:
            return False

        # Gender check
        existing = self.state.get_wrestler(story.participant_ids[0])
        if existing and w.gender != existing.gender:
            raise StoryBuilderError("Cannot mix genders in a story.")

        story.participant_ids.append(wrestler_id)
        w.current_story_id = story.id
        return True

    def remove_participant(
        self,
        story_id: str,
        wrestler_id: str,
    ) -> bool:
        story = self.state.get_storyline(story_id)
        if story is None:
            return False

        if wrestler_id not in story.participant_ids:
            return False

        if len(story.participant_ids) <= 2:
            raise StoryBuilderError("A story needs at least 2 participants.")

        story.participant_ids.remove(wrestler_id)
        w = self.state.get_wrestler(wrestler_id)
        if w and w.current_story_id == story.id:
            w.current_story_id = None
        return True
