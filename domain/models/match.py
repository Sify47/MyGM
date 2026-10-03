"""
Match model - one match on a show card.
"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from core.enums import (
    MatchType,
    MatchImportance,
    CrowdReaction,
    MatchStipulation,
    WinnerMode,
)

class Match:
    def __init__(
        self,
        match_type: MatchType,
        participant_ids: list[str],
        importance: MatchImportance = MatchImportance.MIDCARD,
        championship_id: Optional[str] = None,
        rivalry_id: Optional[str] = None,
        story_id: Optional[str] = None,
        stipulation: MatchStipulation = MatchStipulation.NORMAL,
        winner_mode: WinnerMode = WinnerMode.AUTO,
        winner_override_id: Optional[str] = None,
        match_id: Optional[str] = None,
    ):
        self.id: str = match_id or str(uuid4())
        self.match_type: MatchType = match_type
        self.participant_ids: list[str] = list(participant_ids)
        self.importance: MatchImportance = importance
        self.championship_id: Optional[str] = championship_id
        self.rivalry_id: Optional[str] = rivalry_id
        self.story_id: Optional[str] = story_id
        self.stipulation: MatchStipulation = stipulation
        self.winner_mode: WinnerMode = winner_mode
        self.winner_override_id: Optional[str] = winner_override_id

        # Result
        self.winner_id: Optional[str] = None
        self.rating: int = 0
        self.crowd_reaction: CrowdReaction = CrowdReaction.BORED
        self.story_notes: list[str] = []
    # ===== Serialization =====

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "match_type": self.match_type.value,
            "participant_ids": list(self.participant_ids),
            "importance": self.importance.value,
            "championship_id": self.championship_id,
            "rivalry_id": self.rivalry_id,
            "story_id": self.story_id,
            "stipulation": self.stipulation.value,
            "winner_mode": self.winner_mode.value,
            "winner_override_id": self.winner_override_id,
            "winner_id": self.winner_id,
            "rating": self.rating,
            "crowd_reaction": self.crowd_reaction.value,
            "story_notes": list(self.story_notes),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Match":
        # Backward-compatible enums
        raw_stip = data.get("stipulation", "NORMAL")
        try:
            stipulation = MatchStipulation(raw_stip)
        except ValueError:
            stipulation = MatchStipulation.NORMAL

        raw_mode = data.get("winner_mode", "AUTO")
        try:
            winner_mode = WinnerMode(raw_mode)
        except ValueError:
            winner_mode = WinnerMode.AUTO

        m = cls(
            match_type=MatchType(data["match_type"]),
            participant_ids=data["participant_ids"],
            importance=MatchImportance(data.get("importance", "MIDCARD")),
            championship_id=data.get("championship_id"),
            rivalry_id=data.get("rivalry_id"),
            story_id=data.get("story_id"),
            stipulation=stipulation,
            winner_mode=winner_mode,
            winner_override_id=data.get("winner_override_id"),
            match_id=data.get("id"),
        )
        m.winner_id = data.get("winner_id")
        m.rating = data.get("rating", 0)
        m.crowd_reaction = CrowdReaction(data.get("crowd_reaction", "BORED"))
        m.story_notes = data.get("story_notes", [])
        return m

    def __repr__(self) -> str:
        return f"<Match {self.match_type.value} n={len(self.participant_ids)}>"
