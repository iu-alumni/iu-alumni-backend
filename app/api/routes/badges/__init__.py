from fastapi import APIRouter

from . import catalog, mark_seen, my_badges, other_badges


router = APIRouter()
router.include_router(catalog.router)
router.include_router(my_badges.router)
router.include_router(other_badges.router)
router.include_router(mark_seen.router)
