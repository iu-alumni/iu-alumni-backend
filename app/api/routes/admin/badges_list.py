"""Admin catalog + per-badge award listings.

Powers the admin portal's Badges page:

  GET /api/v1/admin/badges                     — catalog + earned_by counts
  GET /api/v1/admin/badges/{code}/awards       — users holding the badge
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.badge import Badge, UserBadge
from app.models.users import Admin, Alumni


router = APIRouter()


def _criteria_summary(badge: Badge) -> str:
    """Human-readable one-liner describing the badge's award rule."""
    params = badge.params or {}
    strat = badge.strategy

    if strat == "count_threshold":
        metric = params.get("metric", "").replace("_", " ")
        return f"Reach {params.get('threshold', 1)} {metric}".strip()
    if strat == "distinct_count":
        metric = params.get("metric", "").replace("_", " ")
        return f"Reach {params.get('threshold', 1)} {metric}".strip()
    if strat == "year_range":
        lo, hi = params.get("min", "?"), params.get("max", "?")
        return f"Graduation year in {lo}-{hi}"
    if strat == "profile_completeness":
        fields = params.get("fields", [])
        return f"Fill all of: {', '.join(fields)}"
    if strat == "badge_count":
        return f"Earn {params.get('threshold', 10)} badges"
    if strat == "first_n":
        return f"Be among the first {params.get('n', 100)} to pin location"
    if strat == "per_city_first":
        return "Host the first event in a new city"
    if strat == "leaderboard":
        return "Highest yearly attendance in a city (auto-awarded)"
    if strat == "manual":
        return "Manually awarded by an admin"
    return strat


@router.get("/badges", status_code=status.HTTP_200_OK)
def admin_list_badges(
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Every badge in the catalog with its awarded-count and criteria line."""
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    counts_by_badge_id: dict[str, int] = dict(
        db.query(UserBadge.badge_id, func.count(UserBadge.id))
        .group_by(UserBadge.badge_id)
        .all()
    )

    catalog = db.query(Badge).order_by(Badge.tier.asc(), Badge.name.asc()).all()
    return [
        {
            "code": b.code,
            "name": b.name,
            "description": b.description,
            "tier": b.tier,
            "icon_key": b.icon_key,
            "strategy": b.strategy,
            "criteria_summary": _criteria_summary(b),
            "earned_by_count": counts_by_badge_id.get(b.id, 0),
        }
        for b in catalog
    ]


@router.get("/badges/{code}/awards", status_code=status.HTTP_200_OK)
def admin_list_badge_awards(
    code: str,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Users who hold `code`, one row per UserBadge instance.

    Per-instance is important for Local Legend / Founding Host — the same
    badge can be held multiple times with different `extra` metadata (one
    per (city, year) for Local Legend, one per city for Founding Host).
    """
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    badge = db.query(Badge).filter(Badge.code == code).first()
    if badge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Badge not found"
        )

    rows = (
        db.query(UserBadge, Alumni)
        .join(Alumni, Alumni.id == UserBadge.alumni_id)
        .filter(UserBadge.badge_id == badge.id)
        .order_by(UserBadge.awarded_at.desc())
        .all()
    )

    return {
        "code": badge.code,
        "name": badge.name,
        "awards": [
            {
                "alumni_id": alumni.id,
                "first_name": alumni.first_name,
                "last_name": alumni.last_name,
                "email": alumni.email,
                "awarded_at": ub.awarded_at.isoformat() if ub.awarded_at else None,
                "awarded_by": ub.awarded_by,
                "extra": ub.extra or {},
            }
            for ub, alumni in rows
        ],
    }
