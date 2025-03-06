from fastapi import APIRouter
from app.api.routes.authentication import verification, alumni_signup, login

router = APIRouter()

# Include the sub-routers
router.include_router(verification.router)
router.include_router(alumni_signup.router) 
router.include_router(login.router)