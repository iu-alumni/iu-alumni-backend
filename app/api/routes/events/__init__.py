from fastapi import APIRouter

from app.api.routes.events import (
    create_event,
    delete_event,
    event_add_participant,
    event_remove_participant,
    get_event,
    list_event_participants,
    list_events,
    list_owner_events,
    list_participant_events,
    update_event,
)


router = APIRouter()

# fmt: off
# Include the sub-routers - order matters for route precedence!
router.include_router(create_event.router)
router.include_router(list_events.router)
router.include_router(list_owner_events.router)
router.include_router(list_participant_events.router)
router.include_router(get_event.router)
router.include_router(delete_event.router)
router.include_router(event_add_participant.router)
router.include_router(event_remove_participant.router)
router.include_router(list_event_participants.router)
router.include_router(update_event.router)
# fmt: on
