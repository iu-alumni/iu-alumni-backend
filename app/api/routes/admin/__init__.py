from fastapi import APIRouter

from app.api.routes.admin import (
    approve_event,
    badges_award,
    badges_revoke,
    ban,
    decline_event,
    delete_alumni,
    email_diagnostic,
    list_all_events,
    list_all_projects,
    list_banned,
    list_users,
    projects_approve,
    settings,
    unapprove_event,
    unban,
    unverify_user,
    upload_allowed_emails,
    verify_user,
)


router = APIRouter()

router.include_router(ban.router)
router.include_router(unban.router)
router.include_router(delete_alumni.router)
router.include_router(list_banned.router)
router.include_router(list_all_events.router)
router.include_router(approve_event.router)
router.include_router(decline_event.router)
router.include_router(unapprove_event.router)
router.include_router(settings.router)
router.include_router(verify_user.router)
router.include_router(unverify_user.router)
router.include_router(list_users.router)
router.include_router(upload_allowed_emails.router)
router.include_router(email_diagnostic.router)
router.include_router(list_all_projects.router)
router.include_router(projects_approve.router)
router.include_router(badges_award.router)
router.include_router(badges_revoke.router)
