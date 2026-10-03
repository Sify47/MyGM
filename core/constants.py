"""
Non-tunable constants + helper functions.
If it's a number you might want to change for balance, put it in config.py.
If it's a label/string/mapping, put it here.
"""

from core.enums import (
    MoraleState,
    RivalryStage,
    CrowdReaction,
    MatchImportance,
)

# ===== Stat Ranges =====
MIN_STAT = 0
MAX_STAT = 100
MIN_POPULARITY = 0
MAX_POPULARITY = 100
MIN_MORALE = 0
MAX_MORALE = 100
MIN_HEALTH = 0
MAX_HEALTH = 100
MIN_STAMINA = 0
MAX_STAMINA = 100


# ===== Helper: clamp =====
def clamp(value: int, low: int = 0, high: int = 100) -> int:
    """Keep a value inside a range."""
    return max(low, min(high, value))


# ===== Morale State Mapping =====
def morale_state_from_value(value: int) -> MoraleState:
    if value >= 80:
        return MoraleState.HAPPY
    if value >= 50:
        return MoraleState.NEUTRAL
    if value >= 30:
        return MoraleState.UNHAPPY
    return MoraleState.CRITICAL


# ===== Rivalry Stage Mapping (from heat value) =====
def rivalry_stage_from_heat(heat: int) -> RivalryStage:
    if heat <= 20:
        return RivalryStage.NONE
    if heat <= 40:
        return RivalryStage.TENSION
    if heat <= 65:
        return RivalryStage.BUILDING
    if heat <= 85:
        return RivalryStage.HEATED
    return RivalryStage.BLOWOFF


# ===== Crowd Reaction Mapping (from rating 0-100) =====
def crowd_reaction_from_rating(rating: int) -> CrowdReaction:
    if rating < 20:
        return CrowdReaction.DEAD
    if rating < 40:
        return CrowdReaction.BORED
    if rating < 60:
        return CrowdReaction.INTERESTED
    if rating < 80:
        return CrowdReaction.HOT
    return CrowdReaction.ELECTRIC


# ===== Stars from rating =====
def stars_from_rating(rating: int) -> float:
    """
    0-100 rating -> 0.0 - 5.0 stars (half-star increments).
    """
    rating = clamp(rating, 0, 100)
    if rating < 20:
        return 1.0
    if rating < 40:
        return 2.0
    if rating < 60:
        return 3.0
    if rating < 80:
        return 4.0
    return 5.0


# ===== Match Importance Weight (used by Show Rating) =====
IMPORTANCE_WEIGHTS = {
    MatchImportance.OPENER: 0.15,
    MatchImportance.MIDCARD: 0.20,
    MatchImportance.UPPER_CARD: 0.30,
    MatchImportance.MAIN_EVENT: 0.35,
}


# ===== Class vs Class Chemistry Table =====
# Higher = better match chemistry between two wrestlers.
# Symmetric table.
CLASS_CHEMISTRY = {
    ("TECHNICIAN", "TECHNICIAN"): 1.00,
    ("TECHNICIAN", "BRAWLER"): 0.85,
    ("TECHNICIAN", "HIGH_FLYER"): 0.90,
    ("TECHNICIAN", "POWERHOUSE"): 0.80,
    ("TECHNICIAN", "SHOWMAN"): 0.85,
    ("BRAWLER", "BRAWLER"): 0.95,
    ("BRAWLER", "HIGH_FLYER"): 0.85,
    ("BRAWLER", "POWERHOUSE"): 0.95,
    ("BRAWLER", "SHOWMAN"): 0.90,
    ("HIGH_FLYER", "HIGH_FLYER"): 1.00,
    ("HIGH_FLYER", "POWERHOUSE"): 0.85,
    ("HIGH_FLYER", "SHOWMAN"): 0.90,
    ("POWERHOUSE", "POWERHOUSE"): 0.90,
    ("POWERHOUSE", "SHOWMAN"): 0.80,
    ("SHOWMAN", "SHOWMAN"): 0.95,
}


def get_chemistry(class_a: str, class_b: str) -> float:
    """Look up chemistry between two classes (order-independent)."""
    key = (class_a, class_b)
    if key in CLASS_CHEMISTRY:
        return CLASS_CHEMISTRY[key]
    key_rev = (class_b, class_a)
    return CLASS_CHEMISTRY.get(key_rev, 0.85)
