"""
app.py - Application factory and entry point for Qatar Foundation Admin Portal.
"""

import os
from flask import Flask, render_template, jsonify
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import config
from models import db, Admin
from routes.auth_routes import auth_bp
from routes.opportunity_routes import opp_bp


def create_app(config_name: str = "default") -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # -- Configuration --------------------------------------------------------
    app.config.from_object(config[config_name])

    # -- Extensions -----------------------------------------------------------
    db.init_app(app)

    csrf = CSRFProtect()
    csrf.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return Admin.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"success": False, "message": "Authentication required."}), 401

    # -- Blueprints -----------------------------------------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(opp_bp)

    # -- Page routes ----------------------------------------------------------
    @app.route("/")
    def index():
        """Serve the main admin portal page."""
        return render_template("admin.html")

    @app.route("/reset-password")
    def reset_password_page():
        """Serve the reset-password page (same SPA - JS handles routing)."""
        return render_template("admin.html")

    # -- 404 / 405 JSON handlers ----------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "message": "Method not allowed."}), 405

    # -- Database initialisation ----------------------------------------------
    with app.app_context():
        os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)
        db.create_all()
        print("[OK] Database tables created / verified.")

    return app


# -- Entry point --------------------------------------------------------------
if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "development")
    application = create_app(env)

    print("\n" + "=" * 55)
    print("  Qatar Foundation Admin Portal - Flask Backend")
    print("  URL  : http://localhost:5000")
    print("  ENV  : " + env)
    print("=" * 55 + "\n")

    application.run(host="0.0.0.0", port=5000, debug=(env == "development"))
