import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY") or "qf-admin-super-secret-key-change-in-production-2024"

    # ── Database ──────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "sqlite:///" + os.path.join(basedir, "instance", "database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Sessions ──────────────────────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # ── Password Reset ────────────────────────────────────────────────────────
    RESET_TOKEN_EXPIRY_HOURS = 1


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in dev


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # HTTPS only in prod


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
