"""
Main routes - home page, new game, load game.
"""

from flask import Blueprint, render_template, redirect, url_for, request, session

from game.game_manager import GameManager

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    saves = GameManager().saves.list_saves()
    return render_template("index.html", saves=saves)


@main_bp.route("/new", methods=["POST"])
def new_game():
    player_name = (
        request.form.get("player_name", "My Promotion").strip() or "My Promotion"
    )
    gm = GameManager.new_game(player_name=player_name)
    gm.save_game("autosave.json")
    session["save_file"] = "autosave.json"
    return redirect(url_for("game.dashboard"))


@main_bp.route("/load/<filename>")
def load_game(filename: str):
    session["save_file"] = filename
    return redirect(url_for("game.dashboard"))
