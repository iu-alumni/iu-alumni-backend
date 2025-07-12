from fastapi import APIRouter
from app.api.routes.authentication import verification, alumni_signup, login, add_admin, register, verify, resend_verification, request_manual_verification

router = APIRouter()

# Include the sub-routers
router.include_router(register.router)
router.include_router(verify.router)
router.include_router(resend_verification.router)
router.include_router(request_manual_verification.router)
router.include_router(verification.router)
router.include_router(alumni_signup.router) 
router.include_router(login.router)
router.include_router(add_admin.router)