"""
Championship model - WWE-style structure.
"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from core.enums import Division, ChampionshipTier, Gender
from core.constants import clamp


class Championship:
    def __init__(
        self,
        name: str,
        division: Division = Division.MEN,
        tier: ChampionshipTier = ChampionshipTier.TOP,
        prestige: int = 50,
        min_popularity: int = 0,
        champion_id: Optional[str] = None,
        championship_id: Optional[str] = None,
    ):
        self.id: str = championship_id or str(uuid4())
        self.name: str = name
        self.division: Division = division
        self.tier: ChampionshipTier = tier
        self.prestige: int = clamp(prestige)
        self.min_popularity: int = min_popularity
        self.champion_id: Optional[str] = champion_id

        self.defenses: int = 0
        self.days_held: int = 0
        self.weeks_held: int = 0
        self.history: list[dict] = []  # [{"week": 5, "champion_id": "..."}]

    # =========================================================
    # DIVISION HELPERS
    # =========================================================

    def can_compete(self, wrestler) -> bool:
        """
        Check whether a wrestler is eligible to compete for this title.
        """
        if wrestler is None:
            return False

        if self.division == Division.OPEN:
            return True

        if self.division == Division.MEN:
            return wrestler.gender == Gender.MALE

        if self.division == Division.WOMEN:
            return wrestler.gender == Gender.FEMALE

        if self.division == Division.TAG:
            # Tag team titles: check by gender of the team, not the individual.
            # For MVP, we allow anyone here and validate at booking time.
            return True

        return False

    def is_womens_title(self) -> bool:
        return self.division == Division.WOMEN

    def is_mens_title(self) -> bool:
        return self.division == Division.MEN

    def is_tag_title(self) -> bool:
        return self.division == Division.TAG

    # =========================================================
    # METHODS
    # =========================================================

    def change_champion(self, new_champion_id: str, week: int) -> None:
        self.champion_id = new_champion_id
        self.defenses = 0
        self.days_held = 0
        self.weeks_held = 0
        self.history.append(
            {
                "week": week,
                "champion_id": new_champion_id,
            }
        )

    def record_defense(self, prestige_gain: int = 2) -> None:
        self.defenses += 1
        self.prestige = clamp(self.prestige + prestige_gain)

    def tick_week(self) -> None:
        self.weeks_held += 1
        self.days_held += 7
        # Prestige slowly grows with long reigns
        if self.weeks_held % 4 == 0:
            self.prestige = clamp(self.prestige + 1)

    def is_vacant(self) -> bool:
        return self.champion_id is None

    # =========================================================
    # SERIALIZATION
    # =========================================================

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "division": self.division.value,
            "tier": self.tier.value,
            "prestige": self.prestige,
            "min_popularity": self.min_popularity,
            "champion_id": self.champion_id,
            "defenses": self.defenses,
            "days_held": self.days_held,
            "weeks_held": self.weeks_held,
            "history": list(self.history),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Championship":
        # Backward compatibility: old saves had no division/tier
        raw_div = data.get("division", "MEN")
        try:
            division = Division(raw_div)
        except ValueError:
            division = Division.MEN

        raw_tier = data.get("tier", "TOP")
        try:
            tier = ChampionshipTier(raw_tier)
        except ValueError:
            tier = ChampionshipTier.TOP

        c = cls(
            name=data["name"],
            division=division,
            tier=tier,
            prestige=data.get("prestige", 50),
            min_popularity=data.get("min_popularity", 0),
            champion_id=data.get("champion_id"),
            championship_id=data.get("id"),
        )
        c.defenses = data.get("defenses", 0)
        c.days_held = data.get("days_held", 0)
        c.weeks_held = data.get("weeks_held", 0)
        c.history = data.get("history", [])
        return c

    def __repr__(self) -> str:
        return (
            f"<Championship {self.name} "
            f"[{self.division.value}/{self.tier.value}] "
            f"champ={self.champion_id}>"
        )
