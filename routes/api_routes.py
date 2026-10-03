"""
JSON API endpoints for AJAX-driven UI.
"""

from flask import Blueprint, jsonify, session

from game.game_manager import GameManager
from domain.engines import StoryEngine, StoryBuilder

api_bp = Blueprint("api", __name__)


def _load_gm() -> GameManager | None:
    filename = session.get("save_file", "autosave.json")
    return GameManager.load_game(filename)


# ---------------------------------------------------------
# STATE
# ---------------------------------------------------------


@api_bp.route("/state")
def get_state():
    gm = _load_gm()
    if gm is None:
        return jsonify({"error": "no_game"}), 404
    return jsonify(gm.state.to_dict())


# ---------------------------------------------------------
# WRESTLERS
# ---------------------------------------------------------


@api_bp.route("/wrestler/<wrestler_id>")
def get_wrestler(wrestler_id: str):
    gm = _load_gm()
    if gm is None:
        return jsonify({"error": "no_game"}), 404
    w = gm.state.get_wrestler(wrestler_id)
    if w is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify(w.to_dict())


@api_bp.route("/roster")
def get_roster():
    gm = _load_gm()
    if gm is None:
        return jsonify({"error": "no_game"}), 404
    state = gm.state
    return jsonify(
        {
            "all": [w.to_dict() for w in state.roster],
            "male": [w.to_dict() for w in state.roster_male],
            "female": [w.to_dict() for w in state.roster_female],
        }
    )


# ---------------------------------------------------------
# CHAMPIONSHIPS
# ---------------------------------------------------------


@api_bp.route("/championships")
def get_championships():
    gm = _load_gm()
    if gm is None:
        return jsonify({"error": "no_game"}), 404
    return jsonify([c.to_dict() for c in gm.state.championships])


# ---------------------------------------------------------
# STORY SUGGESTIONS
# ---------------------------------------------------------


@api_bp.route("/story/<story_id>/suggest")
def suggest_story_match(story_id: str):
    gm = _load_gm()
    if gm is None:
        return jsonify({"error": "no_game"}), 404

    engine = StoryEngine()
    story = engine.get_story(gm.state, story_id)
    if story is None:
        return jsonify({"error": "not_found"}), 404

    suggestion = engine.suggest_match_for_story(story, gm.state)
    return jsonify(
        {
            "story_id": story.id,
            "participant_ids": story.participant_ids,
            "match_type": suggestion["match_type"],
            "importance": suggestion["importance"],
        }
    )


# ---------------------------------------------------------
# STORY BUILDER HELPERS
# ---------------------------------------------------------


@api_bp.route("/story/<story_id>/beats/suggested")
def get_suggested_beats(story_id: str):
    gm = _load_gm()
    if gm is None:
        return jsonify({"error": "no_game"}), 404

    builder = StoryBuilder(gm.state)
    return jsonify(
        {
            "suggested": builder.get_suggested_beats(story_id),
        }
    )


@api_bp.route("/stories/active")
def get_active_stories():
    gm = _load_gm()
    if gm is None:
        return jsonify({"error": "no_game"}), 404
    return jsonify([s.to_dict() for s in gm.state.get_active_storylines()])


# ---------------------------------------------------------
# RIVALRIES
# ---------------------------------------------------------


@api_bp.route("/rivalries/active")
def get_active_rivalries():
    gm = _load_gm()
    if gm is None:
        return jsonify({"error": "no_game"}), 404
    return jsonify([r.to_dict() for r in gm.state.get_active_rivalries()])
