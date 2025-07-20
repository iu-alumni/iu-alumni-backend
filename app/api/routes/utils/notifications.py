import logging
import os
from urllib.parse import quote

import requests


logger = logging.getLogger(__name__)

BASE_URL = os.getenv(
    "NOTIFICATION_BOT_URL",
    "https://alumap-notification-bot.netlify.app/.netlify/functions",
)
TIMEOUT = 5


def notify_join_event(event_name, owner_alias, user_alias):
    """
    Notify the event owner when a user joins their event

    Args:
        event_name (str): The name of the event
        owner_alias (str): Telegram alias of the event owner
        user_alias (str): Telegram alias of the user who joined
    """
    if not owner_alias or not user_alias:
        logger.warning(
            f"Missing telegram alias for notification: owner={owner_alias}, user={user_alias}"
        )
        return

    # Clean telegram aliases (remove @ if present)
    owner_alias = owner_alias.lstrip("@")
    user_alias = user_alias.lstrip("@")

    # Validate telegram aliases contain only allowed characters
    import re

    if not re.match(r"^[a-zA-Z0-9_]+$", owner_alias) or not re.match(
        r"^[a-zA-Z0-9_]+$", user_alias
    ):
        logger.error(
            f"Invalid telegram alias format: owner={owner_alias}, user={user_alias}"
        )
        return

    try:
        # URL encode the event name to handle special characters
        encoded_event_name = quote(event_name, safe="")
        url = f"{BASE_URL}/notifyJoin/{encoded_event_name}/{owner_alias}/{user_alias}/"
        response = requests.post(url, timeout=TIMEOUT)
        response.raise_for_status()
        logger.info(f"Successfully sent join notification for event '{event_name}'")
    except Exception as e:
        logger.error(f"Failed to send join notification: {e!s}")
        # Don't raise exception to avoid breaking the main flow if notification fails


def notify_admin_manual_verification(user_email: str, user_name: str):
    """
    Notify admins about manual verification request via Telegram

    Args:
        user_email (str): Email of the user requesting verification
        user_name (str): Full name of the user
    """
    message = f"""🔔 Manual Verification Request

Name: {user_name}
Email: {user_email}

You can verify this account via the admin dashboard."""

    try:
        url = f"{BASE_URL}/notifyAdmins"
        data = {"s": message}
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, json=data, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        logger.info(
            f"Successfully sent manual verification notification for {user_email}"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e!s}")
        return False
