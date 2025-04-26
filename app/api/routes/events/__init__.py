from fastapi import APIRouter
from app.api.routes.events import (
    create_event,
    list_events,
    delete_event,
    list_owner_events,
    list_participant_events,
    event_add_participant,
    event_remove_participant,
    list_event_participants,
    update_event,
)

router = APIRouter()

# Include the sub-routers
router.include_router(create_event.router)
router.include_router(list_events.router)
router.include_router(delete_event.router)
router.include_router(list_owner_events.router)
router.include_router(list_participant_events.router)
router.include_router(event_add_participant.router)
router.include_router(event_remove_participant.router)
router.include_router(list_event_participants.router)
router.include_router(update_event.router)