from fastapi import APIRouter
from app.api.routes.admin import ban, unban, list_banned

router = APIRouter()

router.include_router(ban.router)
router.include_router(unban.router)
router.include_router(list_banned.router)