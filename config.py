"""
Global configuration for the game.
Centralizes all tunable numbers so we can balance the game from one place.
"""


class Config:
    # ===== Flask =====
    SECRET_KEY = "wrestling-gm-dev-secret-change-in-prod"
    DEBUG = True

    # ===== Season =====
    SEASON_LENGTH_WEEKS = 12
    PLE_WEEKS = [4, 8, 12]  # Weeks where a PLE happens

    # ===== Roster =====
    ROSTER_SIZE = 20

    # ===== Show =====
    MATCHES_PER_SHOW = 4
    PROMOS_PER_SHOW = 1
    MATCHES_PER_PLE = 6

    # ===== Economy =====
    STARTING_BUDGET = 500_000
    ARENA_COST = 50_000
    PRODUCTION_COST = 20_000

    # ===== Fans =====
    STARTING_FANS = 100_000
    CASUAL_RATIO = 0.7  # 70% casual, 30% hardcore

    # ===== Match Engine Weights (must sum to 1.0) =====
    WEIGHT_SKILL = 0.30
    WEIGHT_POPULARITY = 0.20
    WEIGHT_STORY = 0.20
    WEIGHT_CHEMISTRY = 0.10
    WEIGHT_IMPORTANCE = 0.10
    WEIGHT_CROWD = 0.10

    # Random factor range applied to final match rating
    RANDOM_MIN = -10
    RANDOM_MAX = 10

    # ===== Popularity Changes =====
    POP_WIN = 2
    POP_LOSS = -1
    POP_CHAMPIONSHIP_WIN = 6
    POP_GREAT_MATCH = 3
    POP_BAD_MATCH = -1

    # ===== Morale Changes =====
    MORALE_WIN = 3
    MORALE_LOSS = -2
    MORALE_MAIN_EVENT = 5
    MORALE_LOW_TV_TIME = -3
    MORALE_CHAMPIONSHIP = 8

    # ===== Health / Stamina =====
    HEALTH_NORMAL_MATCH = -5
    HEALTH_MAIN_EVENT = -7
    HEALTH_HIGH_RISK = -10

    STAMINA_MATCH = -10
    STAMINA_MAIN_EVENT = -15
    STAMINA_RECOVERY = 20

    # ===== Rivalry =====
    RIVALRY_HEAT_PROMO = 8
    RIVALRY_HEAT_INTERFERENCE = 15
    RIVALRY_HEAT_TAG = 5
    RIVALRY_HEAT_SINGLES = 10
    RIVALRY_HEAT_BETRAYAL = 25
    RIVALRY_DECAY_NO_INTERACTION = -3

    # ===== Event Probabilities =====
    EVENT_NONE = 0.50
    EVENT_MINOR = 0.30
    EVENT_MAJOR = 0.15
    EVENT_OMG = 0.05

    # ===== Save =====
    SAVE_DIR = "saves"
    SAVE_FILE = "savegame.json"

    # ===== Display =====
    LOG_SIMULATION = True
