"""
Storyline model - a multi-week narrative arc.
Supports both auto-generated and player-built stories.
"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from core.enums import StoryType, StoryBeatType
from core.constants import clamp
from domain.models.story_beat import StoryBeat


class Storyline:
    def __init__(
        self,
        story_type: StoryType,
        participant_ids: list[str],
        title: str = "",
        stage: int = 0,
        heat: int = 30,
        manual_mode: bool = False,
        storyline_id: Optional[str] = None,
    ):
        self.id: str = storyline_id or str(uuid4())
        self.story_type: StoryType = story_type
        self.participant_ids: list[str] = list(participant_ids)
        self.title: str = title or self._default_title()
        self.stage: int = stage
        self.heat: int = clamp(heat)
        self.weeks_active: int = 0
        self.completed: bool = False
        self.manual_mode: bool = manual_mode

        # Stage names
        self.stages: list[str] = self._get_stages()

        # Beats per stage: dict {stage_index: [StoryBeat, ...]}
        self.beats: list[StoryBeat] = []

        # History
        self.history: list[dict] = []

    # =========================================================
    # STAGE NAMES
    # =========================================================

    def _default_title(self) -> str:
        titles = {
            StoryType.UNDERDOG: "The Underdog Story",
            StoryType.CHAMPION_VS_CHALLENGER: "Champion vs Challenger",
            StoryType.BETRAYAL: "Betrayal",
            StoryType.TAG_TEAM_BREAKUP: "Tag Team Breakup",
            StoryType.RISE_OF_A_STAR: "Rise of a Star",
        }
        return titles.get(self.story_type, "Storyline")

    def _get_stages(self) -> list[str]:
        if self.story_type == StoryType.UNDERDOG:
            return ["Introduction", "Struggle", "Momentum", "Shot", "Payoff"]
        if self.story_type == StoryType.CHAMPION_VS_CHALLENGER:
            return ["Callout", "Build", "Doubt", "Face-to-Face", "Title Match"]
        if self.story_type == StoryType.BETRAYAL:
            return ["Alliance", "Cracks", "Tension", "Turn", "Revenge"]
        if self.story_type == StoryType.TAG_TEAM_BREAKUP:
            return ["Unity", "Miscommunication", "Conflict", "Split", "Blowoff"]
        if self.story_type == StoryType.RISE_OF_A_STAR:
            return ["Debut", "First Win", "Statement", "Rivalry", "Breakthrough"]
        return ["Start", "Middle", "End"]

    @property
    def current_stage_name(self) -> str:
        if self.stage >= len(self.stages):
            return "Complete"
        return self.stages[self.stage]

    @property
    def total_stages(self) -> int:
        return len(self.stages)

    # =========================================================
    # BEAT MANAGEMENT
    # =========================================================

    def add_beat(self, beat: StoryBeat) -> None:
        self.beats.append(beat)

    def add_beat_by_type(
        self,
        beat_type: StoryBeatType,
        label: str,
        description: str = "",
        participant_ids: Optional[list[str]] = None,
        custom_text: str = "",
    ) -> StoryBeat:
        beat = StoryBeat(
            beat_type=beat_type,
            label=label,
            description=description,
            participant_ids=participant_ids or list(self.participant_ids),
            custom_text=custom_text,
        )
        self.beats.append(beat)
        return beat

    def complete_beat(self, beat_id: str, week: int) -> bool:
        for beat in self.beats:
            if beat.id == beat_id:
                beat.mark_completed(week)
                self.history.append(
                    {
                        "week": week,
                        "beat_id": beat.id,
                        "beat_label": beat.label,
                        "beat_type": beat.beat_type.value,
                    }
                )
                return True
        return False

    def get_pending_beats(self) -> list[StoryBeat]:
        return [b for b in self.beats if not b.completed]

    def get_completed_beats(self) -> list[StoryBeat]:
        return [b for b in self.beats if b.completed]

    def is_stage_complete(self) -> bool:
        """
        A stage is complete when:
        - auto mode: always True after featured (no beats required)
        - manual mode: all beats must be completed
        """
        if not self.manual_mode:
            return True
        pending = self.get_pending_beats()
        return len(pending) == 0

    # =========================================================
    # STAGE ADVANCEMENT
    # =========================================================

    def advance_stage(self, week: int, note: str = "") -> bool:
        self.stage += 1
        self.history.append(
            {
                "week": week,
                "stage": self.current_stage_name,
                "note": note,
            }
        )
        if self.stage >= len(self.stages):
            self.completed = True
            return True
        return False

    def adjust_heat(self, delta: int) -> None:
        self.heat = clamp(self.heat + delta)

    def involves(self, wrestler_id: str) -> bool:
        return wrestler_id in self.participant_ids

    def is_active(self) -> bool:
        return not self.completed

    # =========================================================
    # SERIALIZATION
    # =========================================================

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "story_type": self.story_type.value,
            "participant_ids": list(self.participant_ids),
            "title": self.title,
            "stage": self.stage,
            "heat": self.heat,
            "weeks_active": self.weeks_active,
            "completed": self.completed,
            "manual_mode": self.manual_mode,
            "stages": list(self.stages),
            "beats": [b.to_dict() for b in self.beats],
            "history": list(self.history),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Storyline":
        s = cls(
            story_type=StoryType(data["story_type"]),
            participant_ids=data["participant_ids"],
            title=data.get("title", ""),
            stage=data.get("stage", 0),
            heat=data.get("heat", 30),
            manual_mode=data.get("manual_mode", False),
            storyline_id=data.get("id"),
        )
        s.weeks_active = data.get("weeks_active", 0)
        s.completed = data.get("completed", False)
        s.stages = data.get("stages", s._get_stages())
        s.beats = [StoryBeat.from_dict(b) for b in data.get("beats", [])]
        s.history = data.get("history", [])
        return s

    def __repr__(self) -> str:
        return (
            f"<Story {self.story_type.value} "
            f"stage={self.stage}/{self.total_stages} "
            f"beats={len(self.beats)}>"
        )
