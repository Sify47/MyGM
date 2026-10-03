"""
Flask entry point for Wrestling GM Simulator.
"""

from flask import Flask
from flask_cors import CORS

from config import Config
from routes.main_routes import main_bp
from routes.game_routes import game_bp
from routes.story_routes import story_bp
from routes.api_routes import api_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    CORS(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(game_bp, url_prefix="/game")
    app.register_blueprint(story_bp, url_prefix="/stories")
    app.register_blueprint(api_bp, url_prefix="/api")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
