"""
Seed data for the MVP roster.

20 real WWE Superstars for the 2026 MVP:
12 male + 8 female.

Game stats are fictional balancing values created for the game.
They are NOT official WWE ratings.

✅ FIX #2: Salaries reduced ~40% to balance economy.
"""

from core.enums import WrestlerClass, Alignment, Gender
from domain.models.wrestler import Wrestler


def seed_roster() -> list[Wrestler]:
    """
    Returns 20 real WWE Superstars:
    12 male + 8 female.
    """

    roster: list[Wrestler] = []

    # =========================================================
    # MEN'S DIVISION — MAIN EVENTERS
    # =========================================================

    roster.append(
        Wrestler(
            name="Roman Reigns",
            gender=Gender.MALE,
            age=41,
            wrestler_class=WrestlerClass.POWERHOUSE,
            alignment=Alignment.FACE,
            popularity=96,
            ring_skill=94,
            mic_skill=94,
            stamina=82,
            morale=90,
            salary=27000,  # كان 45000
            contract_weeks=12,
            potential=94,
            traits=["Top Star", "Main Eventer", "Legendary Presence"],
        )
    )

    roster.append(
        Wrestler(
            name="Cody Rhodes",
            gender=Gender.MALE,
            age=41,
            wrestler_class=WrestlerClass.SHOWMAN,
            alignment=Alignment.FACE,
            popularity=94,
            ring_skill=91,
            mic_skill=94,
            stamina=88,
            morale=88,
            salary=25000,  # كان 42000
            contract_weeks=12,
            potential=92,
            traits=["American Dream", "Main Eventer", "Fan Favorite"],
        )
    )

    roster.append(
        Wrestler(
            name="CM Punk",
            gender=Gender.MALE,
            age=48,
            wrestler_class=WrestlerClass.SHOWMAN,
            alignment=Alignment.HEEL,
            popularity=93,
            ring_skill=91,
            mic_skill=98,
            stamina=72,
            morale=82,
            salary=24000,  # كان 40000
            contract_weeks=12,
            potential=84,
            traits=["Mic Master", "Veteran", "Ego"],
        )
    )

    roster.append(
        Wrestler(
            name="Seth Rollins",
            gender=Gender.MALE,
            age=40,
            wrestler_class=WrestlerClass.SHOWMAN,
            alignment=Alignment.HEEL,
            popularity=91,
            ring_skill=94,
            mic_skill=91,
            stamina=88,
            morale=84,
            salary=23000,  # كان 39000
            contract_weeks=12,
            potential=90,
            traits=["Main Eventer", "Showman", "Big Match Player"],
        )
    )

    # =========================================================
    # MEN'S DIVISION — UPPER MIDCARD
    # =========================================================

    roster.append(
        Wrestler(
            name="Randy Orton",
            gender=Gender.MALE,
            age=46,
            wrestler_class=WrestlerClass.TECHNICIAN,
            alignment=Alignment.FACE,
            popularity=90,
            ring_skill=92,
            mic_skill=88,
            stamina=70,
            morale=82,
            salary=21000,  # كان 35000
            contract_weeks=12,
            potential=80,
            traits=["Veteran", "Legend", "RKO Outta Nowhere"],
        )
    )

    roster.append(
        Wrestler(
            name="Gunther",
            gender=Gender.MALE,
            age=38,
            wrestler_class=WrestlerClass.TECHNICIAN,
            alignment=Alignment.HEEL,
            popularity=89,
            ring_skill=97,
            mic_skill=82,
            stamina=92,
            morale=86,
            salary=23000,  # كان 38000
            contract_weeks=12,
            potential=94,
            traits=["Ring General", "Technical Master", "Dominant"],
        )
    )

    roster.append(
        Wrestler(
            name="Sami Zayn",
            gender=Gender.MALE,
            age=42,
            wrestler_class=WrestlerClass.TECHNICIAN,
            alignment=Alignment.FACE,
            popularity=86,
            ring_skill=90,
            mic_skill=87,
            stamina=84,
            morale=88,
            salary=17000,  # كان 28000
            contract_weeks=12,
            potential=86,
            traits=["Underdog", "Fan Favorite", "Storyteller"],
        )
    )

    roster.append(
        Wrestler(
            name="Kevin Owens",
            gender=Gender.MALE,
            age=42,
            wrestler_class=WrestlerClass.BRAWLER,
            alignment=Alignment.FACE,
            popularity=85,
            ring_skill=89,
            mic_skill=90,
            stamina=82,
            morale=84,
            salary=17000,  # كان 29000
            contract_weeks=12,
            potential=84,
            traits=["Brawler", "Fighter", "Mic Master"],
        )
    )

    # =========================================================
    # MEN'S DIVISION — RISING STARS
    # =========================================================

    roster.append(
        Wrestler(
            name="Jey Uso",
            gender=Gender.MALE,
            age=41,
            wrestler_class=WrestlerClass.HIGH_FLYER,
            alignment=Alignment.FACE,
            popularity=88,
            ring_skill=87,
            mic_skill=88,
            stamina=91,
            morale=91,
            salary=18000,  # كان 30000
            contract_weeks=12,
            potential=89,
            traits=["Yeet", "Fan Favorite", "Tag Specialist"],
        )
    )

    roster.append(
        Wrestler(
            name="Finn Bálor",
            gender=Gender.MALE,
            age=45,
            wrestler_class=WrestlerClass.TECHNICIAN,
            alignment=Alignment.HEEL,
            popularity=83,
            ring_skill=91,
            mic_skill=82,
            stamina=78,
            morale=76,
            salary=16000,  # كان 26000
            contract_weeks=12,
            potential=80,
            traits=["Veteran", "Technical Master", "Mind Games"],
        )
    )

    roster.append(
        Wrestler(
            name="Bron Breakker",
            gender=Gender.MALE,
            age=29,
            wrestler_class=WrestlerClass.POWERHOUSE,
            alignment=Alignment.HEEL,
            popularity=82,
            ring_skill=86,
            mic_skill=76,
            stamina=94,
            morale=82,
            salary=14000,  # كان 24000
            contract_weeks=12,
            potential=97,
            traits=["Powerhouse", "Rising Star", "High Potential"],
        )
    )

    roster.append(
        Wrestler(
            name="Oba Femi",
            gender=Gender.MALE,
            age=28,
            wrestler_class=WrestlerClass.POWERHOUSE,
            alignment=Alignment.HEEL,
            popularity=78,
            ring_skill=84,
            mic_skill=74,
            stamina=95,
            morale=86,
            salary=13000,  # كان 22000
            contract_weeks=12,
            potential=98,
            traits=["Monster", "Dominant", "High Potential"],
        )
    )

    # =========================================================
    # WOMEN'S DIVISION — MAIN EVENTERS
    # =========================================================

    roster.append(
        Wrestler(
            name="Rhea Ripley",
            gender=Gender.FEMALE,
            age=30,
            wrestler_class=WrestlerClass.POWERHOUSE,
            alignment=Alignment.FACE,
            popularity=94,
            ring_skill=94,
            mic_skill=88,
            stamina=90,
            morale=90,
            salary=24000,  # كان 40000
            contract_weeks=12,
            potential=95,
            traits=["Main Eventer", "Powerhouse", "Fan Favorite"],
        )
    )

    roster.append(
        Wrestler(
            name="IYO SKY",
            gender=Gender.FEMALE,
            age=36,
            wrestler_class=WrestlerClass.HIGH_FLYER,
            alignment=Alignment.FACE,
            popularity=88,
            ring_skill=96,
            mic_skill=80,
            stamina=94,
            morale=88,
            salary=18000,  # كان 30000
            contract_weeks=12,
            potential=93,
            traits=["Genius of the Sky", "High Risk", "Crowd Pleaser"],
        )
    )

    roster.append(
        Wrestler(
            name="Tiffany Stratton",
            gender=Gender.FEMALE,
            age=27,
            wrestler_class=WrestlerClass.SHOWMAN,
            alignment=Alignment.HEEL,
            popularity=84,
            ring_skill=86,
            mic_skill=83,
            stamina=91,
            morale=87,
            salary=15000,  # كان 25000
            contract_weeks=12,
            potential=97,
            traits=["Tiffy Time", "Showman", "High Potential"],
        )
    )

    # =========================================================
    # WOMEN'S DIVISION — UPPER MIDCARD
    # =========================================================

    roster.append(
        Wrestler(
            name="Jade Cargill",
            gender=Gender.FEMALE,
            age=34,
            wrestler_class=WrestlerClass.POWERHOUSE,
            alignment=Alignment.HEEL,
            popularity=86,
            ring_skill=84,
            mic_skill=80,
            stamina=92,
            morale=82,
            salary=16000,  # كان 26000
            contract_weeks=12,
            potential=95,
            traits=["Powerhouse", "Athletic", "Dominant"],
        )
    )

    roster.append(
        Wrestler(
            name="Chelsea Green",
            gender=Gender.FEMALE,
            age=35,
            wrestler_class=WrestlerClass.SHOWMAN,
            alignment=Alignment.HEEL,
            popularity=78,
            ring_skill=76,
            mic_skill=91,
            stamina=82,
            morale=84,
            salary=11000,  # كان 18000
            contract_weeks=12,
            potential=85,
            traits=["Comedy", "Heat Magnet", "Character"],
        )
    )

    roster.append(
        Wrestler(
            name="Liv Morgan",
            gender=Gender.FEMALE,
            age=32,
            wrestler_class=WrestlerClass.SHOWMAN,
            alignment=Alignment.HEEL,
            popularity=84,
            ring_skill=84,
            mic_skill=82,
            stamina=88,
            morale=84,
            salary=14000,  # كان 24000
            contract_weeks=12,
            potential=89,
            traits=["Fan Favorite", "Character", "Rising Star"],
        )
    )

    # =========================================================
    # WOMEN'S DIVISION — RISING STARS
    # =========================================================

    roster.append(
        Wrestler(
            name="Sol Ruca",
            gender=Gender.FEMALE,
            age=26,
            wrestler_class=WrestlerClass.HIGH_FLYER,
            alignment=Alignment.FACE,
            popularity=72,
            ring_skill=86,
            mic_skill=68,
            stamina=94,
            morale=88,
            salary=10000,  # كان 16000
            contract_weeks=12,
            potential=96,
            traits=["High Flyer", "Rising Star", "High Potential"],
        )
    )

    roster.append(
        Wrestler(
            name="Raquel Rodriguez",
            gender=Gender.FEMALE,
            age=35,
            wrestler_class=WrestlerClass.POWERHOUSE,
            alignment=Alignment.FACE,
            popularity=80,
            ring_skill=82,
            mic_skill=74,
            stamina=86,
            morale=82,
            salary=13000,  # كان 22000
            contract_weeks=12,
            potential=84,
            traits=["Powerhouse", "Veteran", "Strong Style"],
        )
    )

    # =========================================================
    # SAFETY CHECK
    # =========================================================

    assert len(roster) == 20, f"Roster must have 20 wrestlers, got {len(roster)}"

    males = [w for w in roster if w.gender == Gender.MALE]
    females = [w for w in roster if w.gender == Gender.FEMALE]

    assert len(males) == 12, f"Expected 12 males, got {len(males)}"
    assert len(females) == 8, f"Expected 8 females, got {len(females)}"

    return roster
