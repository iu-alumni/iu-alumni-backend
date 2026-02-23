"""Telegram bot API routes."""

from fastapi import APIRouter

from app.api.routes.telegram import feedback, notifications, webhook


router = APIRouter(prefix="/telegram", tags=["telegram"])

# Include all sub-routers
router.include_router(webhook.router)
router.include_router(notifications.router)
router.include_router(feedback.router)
