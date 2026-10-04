"""
AI Career Operating System & Interview Platform (v2)
-----------------------------------------------------
Application Factory & Blueprint Registration Entrypoint.
Architecture: Clean Layered Design (DB-Ready without a DB)
"""

import os
from flask import Flask
from config import config
from routes import register_blueprints


def calculate_next_difficulty(current_difficulty: str, score: int) -> str:
    """Legacy helper for backward compatibility."""
    current_difficulty = (current_difficulty or "medium").lower()
    if score <= 4:
        if current_difficulty == "hard":
            return "medium"
        return "easy"
    elif score <= 7:
        return current_difficulty
    else:
        if current_difficulty == "easy":
            return "medium"
        return "hard"


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["DEBUG"] = config.DEBUG

    # Initialize SQLite database and demo accounts
    from core.database import init_db, get_user_by_id
    from flask import session, redirect, url_for
    init_db()

    # Register modular blueprints
    register_blueprints(app)

    @app.context_processor
    def inject_current_user():
        user_id = session.get("user_id")
        user = get_user_by_id(user_id) if user_id else None
        return {"current_user": user}

    # Navigation aliases for clean routing
    @app.route("/interviews")
    def interviews_alias():
        return redirect(url_for("interview.hub"))

    @app.route("/learning")
    def learning_alias():
        return redirect(url_for("resources.library"))

    return app


app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port, debug=config.DEBUG)

