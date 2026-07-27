"""Telegram notification helper for badge awards.

One entry point — `notify_badge_awards` — that any code path emitting new
badges can await. Failure-tolerant: any error inside is logged and
swallowed so a Telegram outage never breaks the enclosing request.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logging import app_logger
from app.models.badge import Badge
from app.models.telegram import TelegramUser
from app.models.users import Alumni
from app.services.telegram_bot import telegram_service


async def notify_badge_awards(
    db: Session, alumni: Alumni, badge_codes: list[str]
) -> None:
    """Send a single DM listing the freshly-earned badges.

    No-op unless the user has a verified Telegram alias AND we know their
    chat_id (i.e. they've DM'd the bot at least once). Multiple codes in
    one call collapse to one message per the spec.
    """
    if not badge_codes:
        return
    if not alumni.is_telegram_verified or not alumni.telegram_alias:
        return

    try:
        tg_user = (
            db.query(TelegramUser)
            .filter(TelegramUser.alias == alumni.telegram_alias)
            .first()
        )
        if tg_user is None:
            return

        badges = (
            db.query(Badge).filter(Badge.code.in_(badge_codes)).all()
        )
        if not badges:
            return

        text = _format_message(badges)
        await telegram_service.send_message(chat_id=tg_user.chat_id, text=text)
    except Exception as e:
        app_logger.error(
            "badge notify failed for alumni=%s codes=%s: %s",
            alumni.id,
            badge_codes,
            e,
        )


def _format_message(badges: list[Badge]) -> str:
    if len(badges) == 1:
        b = badges[0]
        return (
            f"🏆 You unlocked the <b>{b.name}</b> badge! "
            f"Open the app to see it."
        )
    lines = [f"• <b>{b.name}</b>" for b in badges]
    return (
        "🏆 You unlocked new badges!\n"
        + "\n".join(lines)
        + "\n\nOpen the app to see them."
    )
