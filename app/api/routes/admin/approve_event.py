from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni


router = APIRouter()


@router.post("/events/approve/{event_id}")
async def approve_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Approve an event"""
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=403, detail="You are not authorized to access this resource"
        )

    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Allow changing approval status even if already set
    if event.approved == True:
        raise HTTPException(status_code=400, detail="Event is already approved")

    event.approved = True
    db.commit()
    db.refresh(event)

    # Badge eval for the host (Founding Host, Host with the most, Rainmaker).
    awarded_codes: list[str] = []
    owner: Alumni | None = None
    try:
        from app.services.badges import award_founding_host, evaluate_for_user

        owner = db.query(Alumni).filter(Alumni.id == event.owner_id).first()
        if owner is not None:
            new_rows = evaluate_for_user(db, owner, "event_approved")
            awarded_codes.extend(r.badge.code for r in new_rows if r.badge)
            fh = award_founding_host(db, owner, event)
            if fh is not None:
                db.commit()
                awarded_codes.append("founding_host")
    except Exception as eval_err:
        import logging
        logging.getLogger("iu_alumni").error(
            "badge eval failed on event_approved: %s", eval_err
        )

    if owner is not None and awarded_codes:
        from app.services.badge_notifications import notify_badge_awards
        await notify_badge_awards(db, owner, awarded_codes)

    return event
