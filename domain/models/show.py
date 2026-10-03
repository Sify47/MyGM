"""
Show model - one weekly show (or PLE).
"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from domain.models.match import Match


class Show:
    def __init__(
        self,
        week: int,
        name: str,
        is_ple: bool = False,
        show_id: Optional[str] = None,
    ):
        self.id: str = show_id or str(uuid4())
        self.week: int = week
        self.name: str = name
        self.is_ple: bool = is_ple

        self.matches: list[Match] = []
        self.promos: list[dict] = []  # {"participant_id": ..., "type": ...}

        # Result
        self.rating: int = 0
        self.expected_attendance: int = 0
        self.actual_attendance: int = 0
        self.revenue: int = 0
        self.expenses: int = 0

    # ===== Serialization =====

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "week": self.week,
            "name": self.name,
            "is_ple": self.is_ple,
            "matches": [m.to_dict() for m in self.matches],
            "promos": list(self.promos),
            "rating": self.rating,
            "expected_attendance": self.expected_attendance,
            "actual_attendance": self.actual_attendance,
            "revenue": self.revenue,
            "expenses": self.expenses,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Show":
        s = cls(
            week=data["week"],
            name=data["name"],
            is_ple=data.get("is_ple", False),
            show_id=data.get("id"),
        )
        s.matches = [Match.from_dict(m) for m in data.get("matches", [])]
        s.promos = data.get("promos", [])
        s.rating = data.get("rating", 0)
        s.expected_attendance = data.get("expected_attendance", 0)
        s.actual_attendance = data.get("actual_attendance", 0)
        s.revenue = data.get("revenue", 0)
        s.expenses = data.get("expenses", 0)
        return s

    def __repr__(self) -> str:
        return f"<Show W{self.week} {self.name} matches={len(self.matches)}>"
