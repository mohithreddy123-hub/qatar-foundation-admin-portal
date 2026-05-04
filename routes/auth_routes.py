"""
routes/auth_routes.py
All authentication-related endpoints:
  POST /api/auth/signup          - register new admin
  POST /api/auth/login           - login
  POST /api/auth/logout          - logout
  GET  /api/auth/me              - return current user info
  POST /api/auth/forgot-password - request password-reset link
  POST /api/auth/reset-password  - apply new password via token
"""

import re
from datetime import datetime

from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import generate_csrf

from models import db, Admin

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# -- helpers ------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def _json_error(msg: str, status: int = 400) -> tuple:
    return jsonify({"success": False, "message": msg}), status


def _json_ok(payload: dict, status: int = 200) -> tuple:
    payload["success"] = True
    return jsonify(payload), status


# -- CSRF TOKEN ---------------------------------------------------------------

@auth_bp.route("/csrf-token", methods=["GET"])
def get_csrf_token():
    return jsonify({"csrf_token": generate_csrf()})


# -- SIGNUP -------------------------------------------------------------------

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}

    full_name        = (data.get("full_name") or "").strip()
    email            = (data.get("email") or "").strip().lower()
    password         = (data.get("password") or "").strip()
    confirm_password = (data.get("confirm_password") or "").strip()

    if not full_name:
        return _json_error("Full name is required.")
    if not email or not _valid_email(email):
        return _json_error("A valid email address is required.")
    if not password or len(password) < 8:
        return _json_error("Password must be at least 8 characters.")
    if password != confirm_password:
        return _json_error("Passwords do not match.")

    if Admin.query.filter_by(email=email).first():
        return _json_error("An account with this email already exists.")

    admin = Admin(full_name=full_name, email=email)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    return _json_ok({"message": "Account created successfully! Please log in."}, 201)


# -- LOGIN --------------------------------------------------------------------

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email    = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    remember = bool(data.get("remember_me", False))

    # Generic error message - never expose whether email exists (security)
    GENERIC_ERR = "Invalid email or password."

    if not email or not _valid_email(email):
        return _json_error(GENERIC_ERR, 401)
    if not password:
        return _json_error(GENERIC_ERR, 401)

    admin = Admin.query.filter_by(email=email).first()
    if not admin or not admin.check_password(password):
        return _json_error(GENERIC_ERR, 401)

    login_user(admin, remember=remember)
    session.permanent = True

    return _json_ok({
        "message": "Login successful!",
        "admin":   admin.to_dict(),
    })


# -- LOGOUT -------------------------------------------------------------------

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return _json_ok({"message": "Signed out successfully."})


# -- CURRENT USER -------------------------------------------------------------

@auth_bp.route("/me", methods=["GET"])
def me():
    if not current_user.is_authenticated:
        return _json_error("Not authenticated.", 401)
    return _json_ok({"admin": current_user.to_dict()})


# -- FORGOT PASSWORD ----------------------------------------------------------

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email or not _valid_email(email):
        return _json_error("A valid email address is required.")

    # Always return the same message - never reveal whether email exists
    SAFE_MSG = (
        "If an account with that email exists, "
        "a reset link has been sent."
    )

    admin = Admin.query.filter_by(email=email).first()
    if admin:
        token      = admin.generate_reset_token(expiry_hours=1)
        reset_link = f"http://localhost:5000/reset-password?token={token}"
        db.session.commit()

        # Log reset link to terminal (no SMTP required in dev)
        print("\n" + "=" * 60)
        print("  PASSWORD RESET LINK (development - check terminal)")
        print(f"  Admin : {admin.email}")
        print(f"  Link  : {reset_link}")
        print(f"  Expiry: 1 hour from now ({datetime.utcnow().strftime('%H:%M UTC')})")
        print("=" * 60 + "\n")

    return _json_ok({"message": SAFE_MSG})


# -- RESET PASSWORD -----------------------------------------------------------

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data             = request.get_json(silent=True) or {}
    token            = (data.get("token") or "").strip()
    new_password     = (data.get("new_password") or "").strip()
    confirm_password = (data.get("confirm_password") or "").strip()

    if not token:
        return _json_error("Reset token is required.")
    if not new_password or len(new_password) < 8:
        return _json_error("Password must be at least 8 characters.")
    if new_password != confirm_password:
        return _json_error("Passwords do not match.")

    admin = Admin.query.filter_by(reset_token=token).first()
    if not admin or not admin.is_reset_token_valid(token):
        return _json_error("Reset link is invalid or has expired.", 400)

    admin.set_password(new_password)
    admin.clear_reset_token()
    db.session.commit()

    return _json_ok({"message": "Password reset successfully! You can now log in."})
