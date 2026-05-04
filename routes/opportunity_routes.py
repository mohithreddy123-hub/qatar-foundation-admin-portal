"""
routes/opportunity_routes.py
────────────────────────────
Full CRUD for opportunities:
  GET    /api/opportunities         — list logged-in admin's opportunities
  POST   /api/opportunities         — create a new opportunity
  GET    /api/opportunities/<id>    — fetch one (owner only)
  PUT    /api/opportunities/<id>    — update (owner only)
  DELETE /api/opportunities/<id>    — delete (owner only)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from models import db, Opportunity, VALID_CATEGORIES

opp_bp = Blueprint("opportunities", __name__, url_prefix="/api/opportunities")

# ── helpers ───────────────────────────────────────────────────────────────────

def _json_error(msg: str, status: int = 400):
    return jsonify({"success": False, "message": msg}), status


def _json_ok(payload: dict, status: int = 200):
    payload["success"] = True
    return jsonify(payload), status


def _get_owned_opportunity(opp_id: int):
    """
    Fetch opportunity by id.
    Returns (opportunity, error_response) — one will always be None.
    Enforces ownership: only the creator admin can access.
    """
    opp = Opportunity.query.get(opp_id)
    if not opp:
        return None, _json_error("Opportunity not found.", 404)
    if opp.admin_id != current_user.id:
        return None, _json_error("Access denied.", 403)
    return opp, None


def _extract_and_validate(data: dict, existing: Opportunity = None):
    """
    Extract + validate opportunity fields from request payload.
    Returns (fields_dict, error_message).  error_message is None on success.
    """
    opportunity_name     = (data.get("opportunity_name") or "").strip()
    duration             = (data.get("duration") or "").strip()
    start_date           = (data.get("start_date") or "").strip()
    description          = (data.get("description") or "").strip()
    skills_to_gain       = (data.get("skills_to_gain") or "").strip()
    category             = (data.get("category") or "").strip().lower()
    future_opportunities = (data.get("future_opportunities") or "").strip()
    max_applicants_raw   = data.get("max_applicants")

    # ── Required-field validation ─────────────────────────────────────────────
    if not opportunity_name:
        return None, "Opportunity name is required."
    if not duration:
        return None, "Duration is required."
    if not start_date:
        return None, "Start date is required."
    if not description:
        return None, "Description is required."
    if not skills_to_gain:
        return None, "Skills to gain is required."
    if not category:
        return None, "Category is required."
    if category not in VALID_CATEGORIES:
        return None, f"Invalid category. Choose from: {', '.join(VALID_CATEGORIES)}."
    if not future_opportunities:
        return None, "Future opportunities field is required."

    # ── Optional integer ──────────────────────────────────────────────────────
    max_applicants = None
    if max_applicants_raw not in (None, "", "0", 0):
        try:
            max_applicants = int(max_applicants_raw)
            if max_applicants < 1:
                return None, "Max applicants must be a positive number."
        except (ValueError, TypeError):
            return None, "Max applicants must be a valid number."

    return {
        "opportunity_name":     opportunity_name,
        "duration":             duration,
        "start_date":           start_date,
        "description":          description,
        "skills_to_gain":       skills_to_gain,
        "category":             category,
        "future_opportunities": future_opportunities,
        "max_applicants":       max_applicants,
    }, None


# ── LIST ──────────────────────────────────────────────────────────────────────

@opp_bp.route("", methods=["GET"])
@login_required
def list_opportunities():
    """Return all opportunities belonging to the logged-in admin."""
    opps = (
        Opportunity.query
        .filter_by(admin_id=current_user.id)
        .order_by(Opportunity.created_at.desc())
        .all()
    )
    return _json_ok({"opportunities": [o.to_dict() for o in opps]})


# ── CREATE ────────────────────────────────────────────────────────────────────

@opp_bp.route("", methods=["POST"])
@login_required
def create_opportunity():
    data = request.get_json(silent=True) or {}
    fields, err = _extract_and_validate(data)
    if err:
        return _json_error(err)

    opp = Opportunity(admin_id=current_user.id, **fields)
    db.session.add(opp)
    db.session.commit()

    return _json_ok(
        {"message": "Opportunity created successfully!", "opportunity": opp.to_dict()},
        201,
    )


# ── READ ONE ──────────────────────────────────────────────────────────────────

@opp_bp.route("/<int:opp_id>", methods=["GET"])
@login_required
def get_opportunity(opp_id: int):
    opp, err = _get_owned_opportunity(opp_id)
    if err:
        return err
    return _json_ok({"opportunity": opp.to_dict()})


# ── UPDATE ────────────────────────────────────────────────────────────────────

@opp_bp.route("/<int:opp_id>", methods=["PUT"])
@login_required
def update_opportunity(opp_id: int):
    opp, err = _get_owned_opportunity(opp_id)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    fields, err = _extract_and_validate(data, existing=opp)
    if err:
        return _json_error(err)

    for key, value in fields.items():
        setattr(opp, key, value)

    db.session.commit()
    return _json_ok({"message": "Opportunity updated successfully!", "opportunity": opp.to_dict()})


# ── DELETE ────────────────────────────────────────────────────────────────────

@opp_bp.route("/<int:opp_id>", methods=["DELETE"])
@login_required
def delete_opportunity(opp_id: int):
    opp, err = _get_owned_opportunity(opp_id)
    if err:
        return err

    db.session.delete(opp)
    db.session.commit()
    return _json_ok({"message": "Opportunity deleted successfully."})
