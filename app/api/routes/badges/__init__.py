from fastapi import APIRouter

from . import catalog, my_badges, other_badges, mark_seen


router = APIRouter()
router.include_router(catalog.router)
router.include_router(my_badges.router)
router.include_router(other_badges.router)
router.include_router(mark_seen.router)
