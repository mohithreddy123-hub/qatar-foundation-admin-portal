from datetime import datetime, timedelta
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─────────────────────────────────────────────────────────────────────────────
#  Admin Model
# ─────────────────────────────────────────────────────────────────────────────
class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Reset-password fields
    reset_token        = db.Column(db.String(128), nullable=True, unique=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # Relationship: one admin → many opportunities
    opportunities = db.relationship(
        "Opportunity", backref="admin", lazy=True, cascade="all, delete-orphan"
    )

    # ── Password helpers ──────────────────────────────────────────────────────
    def set_password(self, password: str) -> None:
        """Hash and store password using Werkzeug's PBKDF2-SHA256."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    # ── Reset-token helpers ───────────────────────────────────────────────────
    def generate_reset_token(self, expiry_hours: int = 1) -> str:
        """Generate a cryptographically secure reset token valid for N hours."""
        token = secrets.token_urlsafe(48)
        self.reset_token        = token
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=expiry_hours)
        return token

    def is_reset_token_valid(self, token: str) -> bool:
        """Return True if the token matches and has not expired."""
        if not self.reset_token or self.reset_token != token:
            return False
        if not self.reset_token_expiry or datetime.utcnow() > self.reset_token_expiry:
            return False
        return True

    def clear_reset_token(self) -> None:
        """Invalidate the reset token after use."""
        self.reset_token        = None
        self.reset_token_expiry = None

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "full_name":  self.full_name,
            "email":      self.email,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Admin {self.email}>"


# ─────────────────────────────────────────────────────────────────────────────
#  Opportunity Model
# ─────────────────────────────────────────────────────────────────────────────
VALID_CATEGORIES = [
    "technology",
    "business",
    "design",
    "marketing",
    "data-science",
    "cybersecurity",
    "cloud",
    "other",
]


class Opportunity(db.Model):
    __tablename__ = "opportunities"

    id                   = db.Column(db.Integer, primary_key=True)
    opportunity_name     = db.Column(db.String(200), nullable=False)
    duration             = db.Column(db.String(100), nullable=False)
    start_date           = db.Column(db.String(50),  nullable=False)   # stored as ISO date string
    description          = db.Column(db.Text,        nullable=False)
    skills_to_gain       = db.Column(db.Text,        nullable=False)   # comma-separated
    category             = db.Column(db.String(50),  nullable=False)
    future_opportunities = db.Column(db.Text,        nullable=False)
    max_applicants       = db.Column(db.Integer,     nullable=True)
    created_at           = db.Column(db.DateTime,    default=datetime.utcnow)

    # Foreign key — links opportunity to its owner admin
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id":                   self.id,
            "opportunity_name":     self.opportunity_name,
            "duration":             self.duration,
            "start_date":           self.start_date,
            "description":          self.description,
            "skills_to_gain":       self.skills_to_gain,
            "category":             self.category,
            "future_opportunities": self.future_opportunities,
            "max_applicants":       self.max_applicants,
            "created_at":           self.created_at.isoformat(),
            "admin_id":             self.admin_id,
        }

    def __repr__(self) -> str:
        return f"<Opportunity {self.opportunity_name}>"
