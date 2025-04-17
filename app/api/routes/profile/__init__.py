from fastapi import APIRouter
from app.api.routes.profile import profile, get_other_profile, get_profiles

router = APIRouter()

# Include the sub-routers
router.include_router(profile.router)
router.include_router(get_profiles.router)
router.include_router(get_other_profile.router)