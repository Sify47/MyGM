"""
Rivalry model - one feud between two wrestlers.
"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from core.enums import RivalryStage
from core.constants import clamp, rivalry_stage_from_heat


class Rivalry:
    def __init__(
        self,
        wrestler_a_id: str,
        wrestler_b_id: str,
        heat: int = 0,
        rivalry_id: Optional[str] = None,
    ):
        self.id: str = rivalry_id or str(uuid4())
        self.wrestler_a_id: str = wrestler_a_id
        self.wrestler_b_id: str = wrestler_b_id
        self.heat: int = clamp(heat)
        self.weeks_active: int = 0
        self.history: list[dict] = (
            []
        )  # [{"week": 3, "event": "promo", "heat_delta": 8}]

    @property
    def stage(self) -> RivalryStage:
        return rivalry_stage_from_heat(self.heat)

    def add_heat(self, delta: int, week: int, event: str) -> None:
        before = self.heat
        self.heat = clamp(self.heat + delta)
        self.history.append(
            {
                "week": week,
                "event": event,
                "heat_delta": self.heat - before,
            }
        )

    def involves(self, wrestler_id: str) -> bool:
        return wrestler_id in (self.wrestler_a_id, self.wrestler_b_id)

    def opponent_of(self, wrestler_id: str) -> Optional[str]:
        if wrestler_id == self.wrestler_a_id:
            return self.wrestler_b_id
        if wrestler_id == self.wrestler_b_id:
            return self.wrestler_a_id
        return None

    def is_active(self) -> bool:
        return self.stage not in (RivalryStage.NONE, RivalryStage.ENDED)

    # ===== Serialization =====

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "wrestler_a_id": self.wrestler_a_id,
            "wrestler_b_id": self.wrestler_b_id,
            "heat": self.heat,
            "weeks_active": self.weeks_active,
            "history": list(self.history),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Rivalry":
        r = cls(
            wrestler_a_id=data["wrestler_a_id"],
            wrestler_b_id=data["wrestler_b_id"],
            heat=data.get("heat", 0),
            rivalry_id=data.get("id"),
        )
        r.weeks_active = data.get("weeks_active", 0)
        r.history = data.get("history", [])
        return r

    def __repr__(self) -> str:
        return f"<Rivalry {self.wrestler_a_id[:4]} vs {self.wrestler_b_id[:4]} heat={self.heat}>"
