from fastapi import APIRouter

from app.api.routes.authentication import (
    add_admin,
    login,
    login_otp,
    login_telegram_otp,
    password_reset_confirm,
    password_reset_request,
    register,
    request_manual_verification,
    resend_verification,
    telegram_verify,
    verify,
)


router = APIRouter()

# Include the sub-routers
router.include_router(register.router)
router.include_router(verify.router)
router.include_router(resend_verification.router)
router.include_router(request_manual_verification.router)
router.include_router(login.router)
router.include_router(login_otp.router)
router.include_router(login_telegram_otp.router)
router.include_router(telegram_verify.router)
router.include_router(password_reset_request.router)
router.include_router(password_reset_confirm.router)
router.include_router(add_admin.router)
