"""
Story routes - Story Builder, Story Detail, Beats management.
"""

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
from domain.engines import StoryBuilder, StoryBuilderError
from core.enums import StoryType, StoryBeatType

story_bp = Blueprint("story", __name__)


# ---------------------------------------------------------
# HELPER
# ---------------------------------------------------------


def _load_gm() -> GameManager | None:
    filename = session.get("save_file", "autosave.json")
    return GameManager.load_game(filename)


def _save_gm(gm: GameManager) -> None:
    gm.save_game(session.get("save_file", "autosave.json"))


# ---------------------------------------------------------
# STORIES LIST
# ---------------------------------------------------------


@story_bp.route("/")
def stories():
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))
    state = gm.state

    active = [s for s in state.storylines if s.is_active()]
    completed = [s for s in state.storylines if not s.is_active()]

    return render_template(
        "stories.html",
        state=state,
        active_stories=active,
        completed_stories=completed,
        story_types=[s.value for s in StoryType],
        beat_types=[b.value for b in StoryBeatType],
    )


# ---------------------------------------------------------
# CREATE STORY
# ---------------------------------------------------------


@story_bp.route("/create", methods=["GET", "POST"])
def create_story():
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))
    state = gm.state

    if request.method == "POST":
        story_type_raw = request.form.get("story_type")
        participant_ids = request.form.getlist("participant_ids")
        title = request.form.get("title", "").strip()

        try:
            story_type = StoryType(story_type_raw)
        except ValueError:
            flash("Invalid story type.", "error")
            return redirect(url_for("story.create_story"))

        if len(participant_ids) < 2:
            flash("Pick at least 2 participants.", "error")
            return redirect(url_for("story.create_story"))

        builder = StoryBuilder(state)
        try:
            story = builder.create_story(
                story_type=story_type,
                participant_ids=participant_ids,
                title=title,
            )
            _save_gm(gm)
            flash(f"Story '{story.title}' created!", "success")
            return redirect(url_for("story.story_detail", story_id=story.id))
        except StoryBuilderError as e:
            flash(str(e), "error")
            return redirect(url_for("story.create_story"))

    # GET: show form
    available = [w for w in state.roster if w.is_available() and not w.current_story_id]
    return render_template(
        "story_create.html",
        state=state,
        available=available,
        story_types=[s.value for s in StoryType],
    )


# ---------------------------------------------------------
# STORY DETAIL
# ---------------------------------------------------------


@story_bp.route("/<story_id>")
def story_detail(story_id: str):
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))
    state = gm.state

    story = state.get_storyline(story_id)
    if story is None:
        flash("Story not found.", "error")
        return redirect(url_for("story.stories"))

    builder = StoryBuilder(state)
    suggested = builder.get_suggested_beats(story_id)

    # Available wrestlers who could be added (same gender, no current story)
    if story.participant_ids:
        first = state.get_wrestler(story.participant_ids[0])
        gender = first.gender if first else None
        addable = [
            w
            for w in state.roster
            if w.is_available()
            and not w.current_story_id
            and (gender is None or w.gender == gender)
        ]
    else:
        addable = []

    return render_template(
        "story_detail.html",
        state=state,
        story=story,
        suggested_beats=suggested,
        addable_wrestlers=addable,
        beat_types=[b.value for b in StoryBeatType],
    )


# ---------------------------------------------------------
# BEAT ACTIONS
# ---------------------------------------------------------


@story_bp.route("/<story_id>/beat/add", methods=["POST"])
def add_beat(story_id: str):
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))

    builder = StoryBuilder(gm.state)

    mode = request.form.get("mode", "library")
    custom_text = request.form.get("custom_text", "").strip()

    try:
        if mode == "library":
            label = request.form.get("beat_label", "").strip()
            if not label:
                flash("Pick a beat from the library.", "error")
                return redirect(url_for("story.story_detail", story_id=story_id))
            builder.add_beat_from_library(story_id, label, custom_text=custom_text)

        elif mode == "custom":
            beat_type_raw = request.form.get("beat_type", "PROMO")
            label = request.form.get("custom_label", "").strip()
            description = request.form.get("custom_description", "").strip()

            if not label:
                flash("Custom beat needs a label.", "error")
                return redirect(url_for("story.story_detail", story_id=story_id))

            try:
                beat_type = StoryBeatType(beat_type_raw)
            except ValueError:
                beat_type = StoryBeatType.PROMO

            builder.add_custom_beat(
                story_id=story_id,
                beat_type=beat_type,
                label=label,
                description=description,
                custom_text=custom_text,
            )

        _save_gm(gm)
        flash("Beat added!", "success")

    except StoryBuilderError as e:
        flash(str(e), "error")

    return redirect(url_for("story.story_detail", story_id=story_id))


@story_bp.route("/<story_id>/beat/<beat_id>/complete", methods=["POST"])
def complete_beat(story_id: str, beat_id: str):
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))

    builder = StoryBuilder(gm.state)
    if builder.complete_beat(story_id, beat_id):
        _save_gm(gm)
        flash("Beat completed!", "success")
    else:
        flash("Could not complete beat.", "error")

    return redirect(url_for("story.story_detail", story_id=story_id))


@story_bp.route("/<story_id>/beat/<beat_id>/remove", methods=["POST"])
def remove_beat(story_id: str, beat_id: str):
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))

    builder = StoryBuilder(gm.state)
    if builder.remove_beat(story_id, beat_id):
        _save_gm(gm)
        flash("Beat removed.", "success")

    return redirect(url_for("story.story_detail", story_id=story_id))


# ---------------------------------------------------------
# STAGE ACTIONS
# ---------------------------------------------------------


@story_bp.route("/<story_id>/advance", methods=["POST"])
def advance_stage(story_id: str):
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))

    builder = StoryBuilder(gm.state)
    if builder.advance_stage_manual(story_id):
        _save_gm(gm)
        flash("Stage advanced!", "success")
    else:
        flash("Could not advance stage.", "error")

    return redirect(url_for("story.story_detail", story_id=story_id))


# ---------------------------------------------------------
# PARTICIPANT ACTIONS
# ---------------------------------------------------------


@story_bp.route("/<story_id>/participant/add", methods=["POST"])
def add_participant(story_id: str):
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))

    wrestler_id = request.form.get("wrestler_id")
    if not wrestler_id:
        flash("Pick a wrestler.", "error")
        return redirect(url_for("story.story_detail", story_id=story_id))

    builder = StoryBuilder(gm.state)
    try:
        if builder.add_participant(story_id, wrestler_id):
            _save_gm(gm)
            flash("Participant added!", "success")
        else:
            flash("Could not add participant.", "error")
    except StoryBuilderError as e:
        flash(str(e), "error")

    return redirect(url_for("story.story_detail", story_id=story_id))


@story_bp.route("/<story_id>/participant/<wrestler_id>/remove", methods=["POST"])
def remove_participant(story_id: str, wrestler_id: str):
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))

    builder = StoryBuilder(gm.state)
    try:
        if builder.remove_participant(story_id, wrestler_id):
            _save_gm(gm)
            flash("Participant removed.", "success")
        else:
            flash("Could not remove participant.", "error")
    except StoryBuilderError as e:
        flash(str(e), "error")

    return redirect(url_for("story.story_detail", story_id=story_id))


# ---------------------------------------------------------
# DELETE STORY
# ---------------------------------------------------------


@story_bp.route("/<story_id>/delete", methods=["POST"])
def delete_story(story_id: str):
    gm = _load_gm()
    if gm is None:
        return redirect(url_for("main.index"))

    builder = StoryBuilder(gm.state)
    if builder.delete_story(story_id):
        _save_gm(gm)
        flash("Story cancelled.", "success")

    return redirect(url_for("story.stories"))
