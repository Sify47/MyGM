"""
TagTeam model — a pair of wrestlers who team together.
"""

from __future__ import annotations

import uuid

from core.enums import Gender, Alignment


class TagTeam:
    def __init__(
        self,
        name: str,
        member_ids: list[str] | None = None,
        gender: Gender = Gender.MALE,
        alignment: Alignment = Alignment.FACE,
        chemistry: int = 50,
        team_id: str | None = None,
        is_empty: bool = False,
    ):
        self.id: str = team_id or str(uuid.uuid4())
        self.name: str = name
        self.member_ids: list[str] = member_ids or []
        self.gender: Gender = gender
        self.alignment: Alignment = alignment
        self.chemistry: int = chemistry
        self.wins: int = 0
        self.losses: int = 0
        self.is_empty: bool = is_empty  # slot فاضي للاعب يعدله

    # ===== Helpers =====

    def is_full(self) -> bool:
        """فريق كامل = 2 أعضاء."""
        return len(self.member_ids) == 2

    def is_valid(self) -> bool:
        """صالح للـbooking: كامل + مش فاضي."""
        return self.is_full() and not self.is_empty

    def has_member(self, wrestler_id: str) -> bool:
        return wrestler_id in self.member_ids

    def record_win(self) -> None:
        self.wins += 1

    def record_loss(self) -> None:
        self.losses += 1

    def adjust_chemistry(self, delta: int) -> None:
        """Chemistry mix: يبدأ random + يتأثر بالنتائج."""
        self.chemistry = max(0, min(100, self.chemistry + delta))

    def win_rate(self) -> float:
        total = self.wins + self.losses
        if total == 0:
            return 0.0
        return self.wins / total

    def __repr__(self) -> str:
        return (
            f"<TagTeam {self.name} "
            f"members={len(self.member_ids)} "
            f"chem={self.chemistry} W/L={self.wins}/{self.losses}>"
        )

    # ===== Serialization =====

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "member_ids": list(self.member_ids),
            "gender": self.gender.value,
            "alignment": self.alignment.value,
            "chemistry": self.chemistry,
            "wins": self.wins,
            "losses": self.losses,
            "is_empty": self.is_empty,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TagTeam":
        return cls(
            name=data["name"],
            member_ids=data.get("member_ids", []),
            gender=Gender(data.get("gender", "MALE")),
            alignment=Alignment(data.get("alignment", "FACE")),
            chemistry=data.get("chemistry", 50),
            team_id=data.get("id"),
            is_empty=data.get("is_empty", False),
        )
