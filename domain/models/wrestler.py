"""
Wrestler model - the core entity of the game.
"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from core.enums import (
    Alignment,
    WrestlerClass,
    MoraleState,
    Gender,
)
from core.constants import (
    clamp,
    morale_state_from_value,
)


class Wrestler:
    def __init__(
        self,
        name: str,
        wrestler_class: WrestlerClass,
        alignment: Alignment,
        gender: Gender = Gender.MALE,
        age: int = 25,
        popularity: int = 50,
        ring_skill: int = 50,
        mic_skill: int = 50,
        stamina: int = 100,
        health: int = 100,
        morale: int = 70,
        salary: int = 5000,
        contract_weeks: int = 12,
        potential: int = 70,
        traits: Optional[list[str]] = None,
        wrestler_id: Optional[str] = None,
    ):
        self.id: str = wrestler_id or str(uuid4())
        self.name: str = name
        self.gender: Gender = gender
        self.age: int = age
        self.wrestler_class: WrestlerClass = wrestler_class
        self.alignment: Alignment = alignment

        self.popularity: int = clamp(popularity)
        self.ring_skill: int = clamp(ring_skill)
        self.mic_skill: int = clamp(mic_skill)
        self.stamina: int = clamp(stamina)
        self.health: int = clamp(health)
        self.morale: int = clamp(morale)
        self.potential: int = clamp(potential)

        self.salary: int = salary
        self.contract_weeks: int = contract_weeks

        self.traits: list[str] = traits or []

        # Runtime state
        self.is_injured: bool = False
        self.injury_weeks: int = 0
        self.wins: int = 0
        self.losses: int = 0
        self.current_rivalry_id: Optional[str] = None
        self.current_story_id: Optional[str] = None
        self.is_champion: bool = False
        self.championship_id: Optional[str] = None

    # =========================================================
    # GENDER HELPERS
    # =========================================================

    def is_male(self) -> bool:
        return self.gender == Gender.MALE

    def is_female(self) -> bool:
        return self.gender == Gender.FEMALE

    def can_face(self, other: "Wrestler") -> bool:
        """Can this wrestler face another in a standard match?"""
        if other is None:
            return False
        return self.gender == other.gender

    # =========================================================
    # DERIVED / HELPERS
    # =========================================================

    @property
    def morale_state(self) -> MoraleState:
        return morale_state_from_value(self.morale)

    def is_available(self) -> bool:
        return not self.is_injured and self.health > 20

    def overall(self) -> int:
        return int(self.ring_skill * 0.5 + self.popularity * 0.3 + self.mic_skill * 0.2)

    def adjust_popularity(self, delta: int) -> int:
        if delta > 0 and self.popularity > 85:
            delta = max(1, delta // 2)
        self.popularity = clamp(self.popularity + delta)
        return self.popularity

    def adjust_morale(self, delta: int) -> int:
        self.morale = clamp(self.morale + delta)
        return self.morale

    def adjust_health(self, delta: int) -> int:
        self.health = clamp(self.health + delta)
        return self.health

    def adjust_stamina(self, delta: int) -> int:
        self.stamina = clamp(self.stamina + delta)
        return self.stamina

    # =========================================================
    # SERIALIZATION
    # =========================================================

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender.value,
            "age": self.age,
            "wrestler_class": self.wrestler_class.value,
            "alignment": self.alignment.value,
            "popularity": self.popularity,
            "ring_skill": self.ring_skill,
            "mic_skill": self.mic_skill,
            "stamina": self.stamina,
            "health": self.health,
            "morale": self.morale,
            "potential": self.potential,
            "salary": self.salary,
            "contract_weeks": self.contract_weeks,
            "traits": list(self.traits),
            "is_injured": self.is_injured,
            "injury_weeks": self.injury_weeks,
            "wins": self.wins,
            "losses": self.losses,
            "current_rivalry_id": self.current_rivalry_id,
            "current_story_id": self.current_story_id,
            "is_champion": self.is_champion,
            "championship_id": self.championship_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Wrestler":
        # Backward compatibility: old saves had gender as string "M"/"F"
        raw_gender = data.get("gender", "MALE")
        if raw_gender in ("M", "MALE", None):
            gender = Gender.MALE
        elif raw_gender in ("F", "FEMALE"):
            gender = Gender.FEMALE
        else:
            gender = Gender.MALE

        w = cls(
            name=data["name"],
            wrestler_class=WrestlerClass(data["wrestler_class"]),
            alignment=Alignment(data["alignment"]),
            gender=gender,
            age=data.get("age", 25),
            popularity=data.get("popularity", 50),
            ring_skill=data.get("ring_skill", 50),
            mic_skill=data.get("mic_skill", 50),
            stamina=data.get("stamina", 100),
            health=data.get("health", 100),
            morale=data.get("morale", 70),
            salary=data.get("salary", 5000),
            contract_weeks=data.get("contract_weeks", 12),
            potential=data.get("potential", 70),
            traits=data.get("traits", []),
            wrestler_id=data.get("id"),
        )
        w.is_injured = data.get("is_injured", False)
        w.injury_weeks = data.get("injury_weeks", 0)
        w.wins = data.get("wins", 0)
        w.losses = data.get("losses", 0)
        w.current_rivalry_id = data.get("current_rivalry_id")
        w.current_story_id = data.get("current_story_id")
        w.is_champion = data.get("is_champion", False)
        w.championship_id = data.get("championship_id")
        return w

    def __repr__(self) -> str:
        return (
            f"<Wrestler {self.name} " f"[{self.gender.value}] " f"OVR={self.overall()}>"
        )
