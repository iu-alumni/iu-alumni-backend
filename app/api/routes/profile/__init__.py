from fastapi import APIRouter
from app.api.routes.profile import profile

router = APIRouter()

# Include the sub-routers
router.include_router(profile.router)