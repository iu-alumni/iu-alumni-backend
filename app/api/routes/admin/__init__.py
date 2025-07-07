from fastapi import APIRouter
from app.api.routes.admin import ban, unban, list_banned, list_all_events, approve_event, decline_event, settings, verify_user, unverify_user, list_users, upload_allowed_emails

router = APIRouter()

router.include_router(ban.router)
router.include_router(unban.router)
router.include_router(list_banned.router)
router.include_router(list_all_events.router)
router.include_router(approve_event.router)
router.include_router(decline_event.router)
router.include_router(settings.router)
router.include_router(verify_user.router)
router.include_router(unverify_user.router)
router.include_router(list_users.router)
router.include_router(upload_allowed_emails.router)