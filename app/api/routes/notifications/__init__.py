from fastapi import APIRouter

from . import list_notifications, unread_count


router = APIRouter()
router.include_router(list_notifications.router)
router.include_router(unread_count.router)
