from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.services.badges import compute_local_legend_winners


router = APIRouter()


@router.post("/badges/recompute-leaderboards", status_code=status.HTTP_200_OK)
def admin_recompute_leaderboards(
    year: int | None = None,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Recompute Local Legend winners for a given year.

    Defaults to the previous calendar year so admins can trigger the
    same computation the cron would have run without passing a param.
    Backfill mode: pass an explicit `year` to award winners for any
    historical year. Idempotent — safe to re-run.
    """
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    target_year = year if year is not None else datetime.utcnow().year - 1
    winners = compute_local_legend_winners(db, target_year)

    return {
        "year": target_year,
        "awarded": len(winners),
    }
