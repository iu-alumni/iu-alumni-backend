from fastapi import APIRouter
from app.api.routes.admin import ban, unban, list_banned, list_all_events, approve_event, decline_event, settings

router = APIRouter()

router.include_router(ban.router)
router.include_router(unban.router)
router.include_router(list_banned.router)
router.include_router(list_all_events.router)
router.include_router(approve_event.router)
router.include_router(decline_event.router)
router.include_router(settings.router)