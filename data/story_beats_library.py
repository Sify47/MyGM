"""
Library of predefined story beats.
Players can pick from these or create custom beats.
"""

from core.enums import StoryBeatType

# =========================================================
# BEAT TEMPLATES
# =========================================================

BEAT_TEMPLATES: list[dict] = [
    # ----- PROMOS -----
    {
        "beat_type": StoryBeatType.PROMO,
        "label": "Cutting Promo",
        "description": "A participant cuts an in-ring promo to build heat.",
    },
    {
        "beat_type": StoryBeatType.PROMO,
        "label": "Hype Package",
        "description": "A video package airs, building anticipation.",
    },
    # ----- CALLOUTS -----
    {
        "beat_type": StoryBeatType.CALLOUT,
        "label": "The Callout",
        "description": "One wrestler publicly calls out another.",
    },
    {
        "beat_type": StoryBeatType.CALLOUT,
        "label": "Challenge Issued",
        "description": "A formal challenge is issued for a future match.",
    },
    # ----- MATCHES -----
    {
        "beat_type": StoryBeatType.MATCH,
        "label": "First Encounter",
        "description": "The two wrestlers meet in the ring for the first time.",
    },
    {
        "beat_type": StoryBeatType.MATCH,
        "label": "Rematch",
        "description": "A rematch is booked with higher stakes.",
    },
    {
        "beat_type": StoryBeatType.MATCH,
        "label": "Tag Team Clash",
        "description": "Both wrestlers team up with allies for a tag match.",
    },
    # ----- INTERFERENCE -----
    {
        "beat_type": StoryBeatType.INTERFERENCE,
        "label": "Distraction",
        "description": "One wrestler interferes in the other's match.",
    },
    {
        "beat_type": StoryBeatType.INTERFERENCE,
        "label": "Costly Mistake",
        "description": "An interference backfires, costing a match.",
    },
    # ----- BETRAYAL -----
    {
        "beat_type": StoryBeatType.BETRAYAL,
        "label": "The Turn",
        "description": "One wrestler betrays the other, turning heel.",
    },
    {
        "beat_type": StoryBeatType.BETRAYAL,
        "label": "Tag Team Split",
        "description": "A tag team dissolves due to betrayal.",
    },
    # ----- ALLIANCE -----
    {
        "beat_type": StoryBeatType.ALLIANCE,
        "label": "Forming an Alliance",
        "description": "Two wrestlers agree to work together (temporarily).",
    },
    {
        "beat_type": StoryBeatType.ALLIANCE,
        "label": "Faction Formation",
        "description": "A new faction is born.",
    },
    # ----- ATTACK -----
    {
        "beat_type": StoryBeatType.ATTACK,
        "label": "Backstage Brawl",
        "description": "A backstage attack ignites the rivalry.",
    },
    {
        "beat_type": StoryBeatType.ATTACK,
        "label": "Ambush",
        "description": "One wrestler ambushes the other in the ring.",
    },
    # ----- RETURN -----
    {
        "beat_type": StoryBeatType.RETURN,
        "label": "Surprise Return",
        "description": "A wrestler returns after an absence.",
    },
    {
        "beat_type": StoryBeatType.RETURN,
        "label": "Unexpected Comeback",
        "description": "A wrestler returns from injury to confront the rival.",
    },
    # ----- CONFRONTATION -----
    {
        "beat_type": StoryBeatType.CONFRONTATION,
        "label": "Face-to-Face",
        "description": "The two wrestlers have a tense face-to-face segment.",
    },
    {
        "beat_type": StoryBeatType.CONFRONTATION,
        "label": "Contract Signing",
        "description": "A contract signing that ends in chaos.",
    },
    # ----- TITLE SHOT -----
    {
        "beat_type": StoryBeatType.TITLE_SHOT,
        "label": "Title Opportunity",
        "description": "A championship match is set up as the story payoff.",
    },
    {
        "beat_type": StoryBeatType.TITLE_SHOT,
        "label": "Title Match",
        "description": "The championship match that ends the story.",
    },
]


# =========================================================
# STORY STAGE SUGGESTIONS
# =========================================================

# For each story type, which beats fit which stage?

STORY_STAGE_BEATS: dict[str, list[list[str]]] = {
    "UNDERDOG": [
        ["Cutting Promo", "Hype Package"],
        ["Challenge Issued", "First Encounter"],
        ["Distraction", "Backstage Brawl"],
        ["Face-to-Face", "Rematch"],
        ["Title Opportunity", "Title Match"],
    ],
    "CHAMPION_VS_CHALLENGER": [
        ["The Callout", "Challenge Issued"],
        ["Cutting Promo", "Face-to-Face"],
        ["Ambush", "Rematch"],
        ["Contract Signing", "Face-to-Face"],
        ["Title Match", "Title Opportunity"],
    ],
    "BETRAYAL": [
        ["Forming an Alliance", "Cutting Promo"],
        ["Costly Mistake", "Backstage Brawl"],
        ["Distraction", "Ambush"],
        ["The Turn", "Tag Team Split"],
        ["Rematch", "Title Match"],
    ],
    "TAG_TEAM_BREAKUP": [
        ["Forming an Alliance", "Cutting Promo"],
        ["Costly Mistake", "Distraction"],
        ["Backstage Brawl", "Face-to-Face"],
        ["Tag Team Split", "The Turn"],
        ["Rematch", "Face-to-Face"],
    ],
    "RISE_OF_A_STAR": [
        ["Cutting Promo", "Hype Package"],
        ["First Encounter", "Rematch"],
        ["Cutting Promo", "Face-to-Face"],
        ["Backstage Brawl", "Title Opportunity"],
        ["Title Match", "Face-to-Face"],
    ],
}


# =========================================================
# LOOKUP HELPERS
# =========================================================


def get_all_templates() -> list[dict]:
    return list(BEAT_TEMPLATES)


def get_templates_by_type(beat_type: StoryBeatType) -> list[dict]:
    return [t for t in BEAT_TEMPLATES if t["beat_type"] == beat_type]


def get_template_by_label(label: str) -> dict | None:
    for t in BEAT_TEMPLATES:
        if t["label"] == label:
            return t
    return None


def get_suggested_beats_for_stage(
    story_type: str,
    stage_index: int,
) -> list[str]:
    """Return list of beat labels suggested for a given stage."""
    stages = STORY_STAGE_BEATS.get(story_type, [])
    if stage_index >= len(stages):
        return []
    return stages[stage_index]
