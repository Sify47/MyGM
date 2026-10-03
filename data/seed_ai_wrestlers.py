"""
Seed data for the AI promotion's roster.

12 fictional wrestlers (8 male + 4 female) with original names.
Designed to feel like a rival WWE-style promotion.

✅ Batch 10.a
"""

from core.enums import WrestlerClass, Alignment, Gender
from domain.models.wrestler import Wrestler


def seed_ai_roster() -> list[Wrestler]:
    """
    Returns 12 AI wrestlers: 8 male + 4 female.
    """
    roster: list[Wrestler] = []

    # =========================================================
    # MEN — MAIN EVENTERS
    # =========================================================

    roster.append(
        Wrestler(
            name="Diesel Kane",
            gender=Gender.MALE,
            age=38,
            wrestler_class=WrestlerClass.POWERHOUSE,
            alignment=Alignment.HEEL,
            popularity=92,
            ring_skill=90,
            mic_skill=88,
            stamina=85,
            morale=88,
            salary=25000,
            contract_weeks=12,
            potential=90,
            traits=["Monster", "Main Eventer", "Dominant"],
        )
    )

    roster.append(
        Wrestler(
            name="Viper Nova",
            gender=Gender.MALE,
            age=35,
            wrestler_class=WrestlerClass.TECHNICIAN,
            alignment=Alignment.FACE,
            popularity=90,
            ring_skill=95,
            mic_skill=86,
            stamina=90,
            morale=86,
            salary=23000,
            contract_weeks=12,
            potential=92,
            traits=["Ring General", "Technical Master", "Crowd Favorite"],
        )
    )

    # =========================================================
    # MEN — UPPER MIDCARD
    # =========================================================

    roster.append(
        Wrestler(
            name="Axel Steel",
            gender=Gender.MALE,
            age=32,
            wrestler_class=WrestlerClass.BRAWLER,
            alignment=Alignment.HEEL,
            popularity=84,
            ring_skill=86,
            mic_skill=82,
            stamina=88,
            morale=84,
            salary=18000,
            contract_weeks=12,
            potential=88,
            traits=["Brawler", "Fighter", "No Nonsense"],
        )
    )

    roster.append(
        Wrestler(
            name="Jet Kaito",
            gender=Gender.MALE,
            age=29,
            wrestler_class=WrestlerClass.HIGH_FLYER,
            alignment=Alignment.FACE,
            popularity=82,
            ring_skill=89,
            mic_skill=78,
            stamina=93,
            morale=88,
            salary=16000,
            contract_weeks=12,
            potential=92,
            traits=["High Flyer", "Rising Star", "Crowd Pleaser"],
        )
    )

    roster.append(
        Wrestler(
            name="Marcus Cole",
            gender=Gender.MALE,
            age=40,
            wrestler_class=WrestlerClass.SHOWMAN,
            alignment=Alignment.HEEL,
            popularity=86,
            ring_skill=84,
            mic_skill=94,
            stamina=78,
            morale=82,
            salary=19000,
            contract_weeks=12,
            potential=82,
            traits=["Mic Master", "Veteran", "Showman"],
        )
    )

    # =========================================================
    # MEN — RISING STARS
    # =========================================================

    roster.append(
        Wrestler(
            name="Thunder Reyes",
            gender=Gender.MALE,
            age=26,
            wrestler_class=WrestlerClass.POWERHOUSE,
            alignment=Alignment.FACE,
            popularity=76,
            ring_skill=82,
            mic_skill=72,
            stamina=94,
            morale=88,
            salary=13000,
            contract_weeks=12,
            potential=96,
            traits=["Rising Star", "Powerhouse", "High Potential"],
        )
    )

    roster.append(
        Wrestler(
            name="Cipher",
            gender=Gender.MALE,
            age=30,
            wrestler_class=WrestlerClass.TECHNICIAN,
            alignment=Alignment.HEEL,
            popularity=78,
            ring_skill=88,
            mic_skill=80,
            stamina=88,
            morale=80,
            salary=15000,
            contract_weeks=12,
            potential=90,
            traits=["Technical Master", "Mind Games", "Mysterious"],
        )
    )

    roster.append(
        Wrestler(
            name="Bruno Stone",
            gender=Gender.MALE,
            age=33,
            wrestler_class=WrestlerClass.BRAWLER,
            alignment=Alignment.FACE,
            popularity=80,
            ring_skill=85,
            mic_skill=76,
            stamina=86,
            morale=84,
            salary=16000,
            contract_weeks=12,
            potential=86,
            traits=["Brawler", "Fan Favorite", "Fighter"],
        )
    )

    # =========================================================
    # WOMEN — MAIN EVENTERS
    # =========================================================

    roster.append(
        Wrestler(
            name="Vera Vex",
            gender=Gender.FEMALE,
            age=31,
            wrestler_class=WrestlerClass.POWERHOUSE,
            alignment=Alignment.HEEL,
            popularity=91,
            ring_skill=92,
            mic_skill=86,
            stamina=90,
            morale=88,
            salary=22000,
            contract_weeks=12,
            potential=93,
            traits=["Main Eventer", "Dominant", "Fearless"],
        )
    )

    roster.append(
        Wrestler(
            name="Luna Frost",
            gender=Gender.FEMALE,
            age=28,
            wrestler_class=WrestlerClass.HIGH_FLYER,
            alignment=Alignment.FACE,
            popularity=88,
            ring_skill=94,
            mic_skill=82,
            stamina=93,
            morale=88,
            salary=19000,
            contract_weeks=12,
            potential=95,
            traits=["High Flyer", "Crowd Pleaser", "Rising Star"],
        )
    )

    # =========================================================
    # WOMEN — UPPER MIDCARD / RISING
    # =========================================================

    roster.append(
        Wrestler(
            name="Nadia Storm",
            gender=Gender.FEMALE,
            age=26,
            wrestler_class=WrestlerClass.TECHNICIAN,
            alignment=Alignment.HEEL,
            popularity=80,
            ring_skill=87,
            mic_skill=78,
            stamina=90,
            morale=84,
            salary=14000,
            contract_weeks=12,
            potential=96,
            traits=["Technical Master", "Rising Star", "High Potential"],
        )
    )

    roster.append(
        Wrestler(
            name="Roxy Wild",
            gender=Gender.FEMALE,
            age=33,
            wrestler_class=WrestlerClass.SHOWMAN,
            alignment=Alignment.FACE,
            popularity=82,
            ring_skill=82,
            mic_skill=88,
            stamina=85,
            morale=86,
            salary=16000,
            contract_weeks=12,
            potential=87,
            traits=["Showman", "Charismatic", "Fan Favorite"],
        )
    )

    # =========================================================
    # SAFETY CHECK
    # =========================================================

    assert len(roster) == 12, f"AI roster must have 12 wrestlers, got {len(roster)}"

    males = [w for w in roster if w.gender == Gender.MALE]
    females = [w for w in roster if w.gender == Gender.FEMALE]

    assert len(males) == 8, f"Expected 8 AI males, got {len(males)}"
    assert len(females) == 4, f"Expected 4 AI females, got {len(females)}"

    return roster
