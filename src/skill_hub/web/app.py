"""Flask app factory."""
from pathlib import Path

from flask import Flask, render_template

from skill_hub.web.api import api_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
