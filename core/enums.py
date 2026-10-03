"""
All game enums live here.
"""

from enum import Enum

# =========================================================
# WRESTLER-RELATED ENUMS
# =========================================================


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class Alignment(str, Enum):
    FACE = "FACE"
    HEEL = "HEEL"
    TWEENER = "TWEENER"


class WrestlerClass(str, Enum):
    TECHNICIAN = "TECHNICIAN"
    BRAWLER = "BRAWLER"
    HIGH_FLYER = "HIGH_FLYER"
    POWERHOUSE = "POWERHOUSE"
    SHOWMAN = "SHOWMAN"


# =========================================================
# MATCH-RELATED ENUMS
# =========================================================


class MatchType(str, Enum):
    SINGLES = "SINGLES"
    TAG_TEAM = "TAG_TEAM"
    TRIPLE_THREAT = "TRIPLE_THREAT"
    FATAL_4_WAY = "FATAL_4_WAY"
    CHAMPIONSHIP = "CHAMPIONSHIP"


class MatchImportance(str, Enum):
    OPENER = "OPENER"
    MIDCARD = "MIDCARD"
    UPPER_CARD = "UPPER_CARD"
    MAIN_EVENT = "MAIN_EVENT"


class MatchStipulation(str, Enum):
    """Special match rules."""

    NORMAL = "NORMAL"
    NO_DQ = "NO_DQ"
    HARDCORE = "HARDCORE"
    LADDER = "LADDER"
    STEEL_CAGE = "STEEL_CAGE"
    SUBMISSION = "SUBMISSION"
    FALLS_COUNT_ANYWHERE = "FALLS_COUNT_ANYWHERE"


class WinnerMode(str, Enum):
    """How the winner is decided."""

    AUTO = "AUTO"  # Engine decides
    MANUAL = "MANUAL"  # Player picks


# =========================================================
# RIVALRY / STORY ENUMS
# =========================================================


class RivalryStage(str, Enum):
    NONE = "NONE"
    TENSION = "TENSION"
    BUILDING = "BUILDING"
    HEATED = "HEATED"
    BLOWOFF = "BLOWOFF"
    ENDED = "ENDED"


class StoryType(str, Enum):
    UNDERDOG = "UNDERDOG"
    CHAMPION_VS_CHALLENGER = "CHAMPION_VS_CHALLENGER"
    BETRAYAL = "BETRAYAL"
    TAG_TEAM_BREAKUP = "TAG_TEAM_BREAKUP"
    RISE_OF_A_STAR = "RISE_OF_A_STAR"


class StoryBeatType(str, Enum):
    """Types of story beats the player can add manually."""

    PROMO = "PROMO"
    CALLOUT = "CALLOUT"
    MATCH = "MATCH"
    INTERFERENCE = "INTERFERENCE"
    BETRAYAL = "BETRAYAL"
    ALLIANCE = "ALLIANCE"
    ATTACK = "ATTACK"
    RETURN = "RETURN"
    CONFRONTATION = "CONFRONTATION"
    TITLE_SHOT = "TITLE_SHOT"


# =========================================================
# STATE ENUMS
# =========================================================


class MoraleState(str, Enum):
    HAPPY = "HAPPY"
    NEUTRAL = "NEUTRAL"
    UNHAPPY = "UNHAPPY"
    CRITICAL = "CRITICAL"


class EventSeverity(str, Enum):
    NONE = "NONE"
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    OMG = "OMG"


class CrowdReaction(str, Enum):
    DEAD = "DEAD"
    BORED = "BORED"
    INTERESTED = "INTERESTED"
    HOT = "HOT"
    ELECTRIC = "ELECTRIC"


# =========================================================
# CHAMPIONSHIP ENUMS
# =========================================================


class Division(str, Enum):
    """Which division a championship belongs to."""

    MEN = "MEN"
    WOMEN = "WOMEN"
    TAG = "TAG"
    OPEN = "OPEN"  # Intergender (rare, not used by default)


class ChampionshipTier(str, Enum):
    """Importance level of a championship."""

    TOP = "TOP"  # World title
    MID = "MID"  # Intercontinental / US
    TAG = "TAG"  # Tag team
    SPECIAL = "SPECIAL"  # 24/7, Hardcore, etc.

# في core/enums.py


class AIPersonality(Enum):
    """AI GM personality — affects booking style."""

    AGGRESSIVE = "AGGRESSIVE"  # Hardcore matches, intense feuds
    BALANCED = "BALANCED"  # Even distribution
    SHOWMAN = "SHOWMAN"  # Big main events, promos
    TECHNICAL = "TECHNICAL"  # Pure wrestling, long matches
    CHAOTIC = "CHAOTIC"  # Unpredictable, random
