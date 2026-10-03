"""
Game routes - dashboard, roster, booking, simulation, results.
"""

import json

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request,
)

from game.game_manager import GameManager
from game.booking_manager import BookingError
from core.enums import (
    MatchType,
    MatchImportance,
    MatchStipulation,
    WinnerMode,
    Division,
)
from domain.engines import StoryEngine

game_bp = Blueprint("game", __name__)


# ---------------------------------------------------------
# HELPER
# ---------------------------------------------------------


def _load_gm() -> GameManager | None:
    filename = session.get("save_file", "autosave.json")
    return GameManager.load_game(filename)


def _save_gm(gm: GameManager) -> None:
    gm.save_game(session.get("save_file", "autosave.json"))


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------


@game_bp.route("/dashboard")
def dashboard():
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))
    state = gm.state
    return render_template(
        "dashboard.html",
        state=state,
        championships=state.championships,
        active_rivalries=state.get_active_rivalries(),
        active_stories=state.get_active_storylines(),
        recent_news=state.news[-5:][::-1],
    )


# ---------------------------------------------------------
# ROSTER
# ---------------------------------------------------------


@game_bp.route("/roster")
def roster():
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))
    state = gm.state
    sorted_roster = sorted(state.roster, key=lambda w: w.popularity, reverse=True)
    return render_template(
        "roster.html",
        state=state,
        roster=sorted_roster,
    )


# ---------------------------------------------------------
# BOOKING
# ---------------------------------------------------------


@game_bp.route("/booking", methods=["GET", "POST"])
def booking():
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))
    state = gm.state

    story_engine = StoryEngine()
    active_stories = story_engine.get_active_stories(state)

    # ===== POST actions =====
    if request.method == "POST":
        action = request.form.get("action")

        if action == "auto":
            show = gm.auto_build_show()
            session["current_show"] = _show_to_session(show)
            return redirect(url_for("game.booking"))

        if action == "clear":
            session.pop("current_show", None)
            return redirect(url_for("game.booking"))

        if action == "save_and_simulate":
            card_json = request.form.get("card_json", "[]")
            try:
                card = json.loads(card_json)
            except json.JSONDecodeError:
                card = []

            show = gm.booking.create_show()
            errors = []
            for entry in card:
                pids = entry.get("participant_ids", [])
                importance_raw = entry.get("importance", "MIDCARD")
                match_type_raw = entry.get("match_type", "SINGLES")
                stipulation_raw = entry.get("stipulation", "NORMAL")
                championship_id = entry.get("championship_id") or None
                story_id = entry.get("story_id") or None
                winner_mode_raw = entry.get("winner_mode", "AUTO")
                winner_override_id = entry.get("winner_override_id") or None

                try:
                    match_type = MatchType(match_type_raw)
                    importance = MatchImportance(importance_raw)
                    stipulation = MatchStipulation(stipulation_raw)
                    winner_mode = WinnerMode(winner_mode_raw)
                except ValueError as e:
                    errors.append(f"Invalid enum: {e}")
                    continue

                try:
                    gm.booking.add_match(
                        show,
                        match_type=match_type,
                        participant_ids=pids,
                        importance=importance,
                        championship_id=championship_id,
                        story_id=story_id,
                        stipulation=stipulation,
                        winner_mode=winner_mode,
                        winner_override_id=winner_override_id,
                    )
                except BookingError as e:
                    errors.append(str(e))

            for err in errors:
                flash(err, "error")

            if not show.matches:
                flash("No valid matches booked.", "error")
                return redirect(url_for("game.booking"))

            result = gm.simulate_player_show(show)
            ai_result = gm.run_ai_turn()
            week_result = gm.end_week()
            _save_gm(gm)

            session["last_show_result"] = {
                "show_rating": result["show_rating"],
                "economy": result["economy"],
                "match_count": len(result["matches"]),
                "ai_rating": ai_result["ai_show_rating"],
                "week_event": week_result.get("event"),
            }
            return redirect(url_for("game.results"))

    # ===== GET: build or restore =====
    if "current_show" in session:
        show = _session_to_show(session["current_show"])
    else:
        show = gm.booking.create_show()
        session["current_show"] = _show_to_session(show)

    # Split available by gender
    available_male = [
        w
        for w in state.roster
        if w.is_available() and w.contract_weeks > 0 and w.gender.value == "MALE"
    ]
    available_female = [
        w
        for w in state.roster
        if w.is_available() and w.contract_weeks > 0 and w.gender.value == "FEMALE"
    ]

    return render_template(
        "booking.html",
        state=state,
        show=show,
        available_male=available_male,
        available_female=available_female,
        active_stories=active_stories,
        match_types=[m.value for m in MatchType],
        importance_levels=[i.value for i in MatchImportance],
        stipulations=[s.value for s in MatchStipulation],
        championships=state.championships,
    )


# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------


@game_bp.route("/results")
def results():
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))
    state = gm.state
    result = session.pop("last_show_result", None)
    last_show = state.shows[-1] if state.shows else None
    return render_template(
        "results.html",
        state=state,
        result=result,
        show=last_show,
    )


# ---------------------------------------------------------
# SEASON SUMMARY
# ---------------------------------------------------------


@game_bp.route("/season")
def season():
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))
    summary = gm.season_summary() if gm.is_season_over() else None
    return render_template(
        "season.html",
        state=gm.state,
        summary=summary,
    )


# ---------------------------------------------------------
# SESSION HELPERS
# ---------------------------------------------------------


def _show_to_session(show) -> dict:
    return {
        "id": show.id,
        "week": show.week,
        "name": show.name,
        "is_ple": show.is_ple,
        "matches": [m.to_dict() for m in show.matches],
    }


def _session_to_show(data: dict):
    from domain.models.show import Show
    from domain.models.match import Match

    show = Show(
        week=data["week"],
        name=data["name"],
        is_ple=data["is_ple"],
        show_id=data["id"],
    )
    show.matches = [Match.from_dict(m) for m in data["matches"]]
    return show
