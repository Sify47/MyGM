"""
Story Beat model - a single event/action inside a storyline.
Beats can be:
- Library beats (predefined)
- Custom beats (player-written promo text, etc.)
"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from core.enums import StoryBeatType


class StoryBeat:
    def __init__(
        self,
        beat_type: StoryBeatType,
        label: str,
        description: str = "",
        participant_ids: Optional[list[str]] = None,
        custom_text: str = "",
        completed: bool = False,
        week_completed: Optional[int] = None,
        beat_id: Optional[str] = None,
    ):
        self.id: str = beat_id or str(uuid4())
        self.beat_type: StoryBeatType = beat_type
        self.label: str = label  # Short name: "The Callout"
        self.description: str = description  # What happens
        self.participant_ids: list[str] = list(participant_ids or [])
        self.custom_text: str = custom_text  # Player's own text (optional)
        self.completed: bool = completed
        self.week_completed: Optional[int] = week_completed

    # =========================================================
    # HELPERS
    # =========================================================

    def mark_completed(self, week: int) -> None:
        self.completed = True
        self.week_completed = week

    def involves(self, wrestler_id: str) -> bool:
        return wrestler_id in self.participant_ids

    # =========================================================
    # SERIALIZATION
    # =========================================================

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "beat_type": self.beat_type.value,
            "label": self.label,
            "description": self.description,
            "participant_ids": list(self.participant_ids),
            "custom_text": self.custom_text,
            "completed": self.completed,
            "week_completed": self.week_completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StoryBeat":
        return cls(
            beat_type=StoryBeatType(data["beat_type"]),
            label=data.get("label", ""),
            description=data.get("description", ""),
            participant_ids=data.get("participant_ids", []),
            custom_text=data.get("custom_text", ""),
            completed=data.get("completed", False),
            week_completed=data.get("week_completed"),
            beat_id=data.get("id"),
        )

    def __repr__(self) -> str:
        status = "✓" if self.completed else "○"
        return f"<Beat {status} {self.beat_type.value}: {self.label}>"
