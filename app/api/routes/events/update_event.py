from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.utils.notifications import notify_event_updated
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.events import Event
from app.models.users import Admin, Alumni
from app.schemas.event import Event as EventResponse, UpdateEventRequest


router = APIRouter()


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    event_data: UpdateEventRequest,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """
    Update an event. Only the event owner or an admin can update an event.
    """
    # Retrieve the event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    # Check if user is authorized (event owner or admin)
    is_admin = isinstance(current_user, Admin)
    is_owner = event.owner_id == current_user.id

    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this event",
        )

    # Track changes for notifications
    changes = {}

    # Store old values for important fields
    old_location = event.location
    old_datetime = event.datetime
    old_cost = event.cost
    old_is_online = event.is_online

    # Update fields if provided
    if event_data.title is not None:
        event.title = event_data.title

    if event_data.description is not None:
        event.description = event_data.description

    if event_data.location is not None and event_data.location != old_location:
        event.location = event_data.location
        changes["location"] = event_data.location

    if event_data.datetime is not None and event_data.datetime != old_datetime:
        event.datetime = event_data.datetime
        changes["datetime"] = event_data.datetime.strftime("%Y-%m-%d %H:%M")

    if event_data.cost is not None and event_data.cost != old_cost:
        event.cost = event_data.cost
        changes["cost"] = event_data.cost

    if event_data.is_online is not None and event_data.is_online != old_is_online:
        event.is_online = event_data.is_online
        changes["is_online"] = event_data.is_online

    if event_data.cover is not None:
        event.cover = event_data.cover

    # Commit changes
    db.commit()
    db.refresh(event)

    # Send notifications if important fields changed and event is approved
    if changes and event.approved:
        # Get event owner
        owner = db.query(Alumni).filter(Alumni.id == event.owner_id).first()

        # Get all users to notify (participants + owner)
        users_to_notify = set(event.participants_ids)
        if owner:
            users_to_notify.add(owner.id)

        # Send notifications to all users
        for user_id in users_to_notify:
            user = db.query(Alumni).filter(Alumni.id == user_id).first()
            if user and user.telegram_alias:
                notify_event_updated(
                    event_name=event.title,
                    user_alias=user.telegram_alias,
                    changes=changes,
                )

    return event
