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


def notify_event_reminder(
    event_name: str,
    user_alias: str,
    event_datetime: str,
    location: str,
    is_online: bool,
):
    """
    Send 12-hour reminder notification to event participant

    Args:
        event_name (str): Name of the event
        user_alias (str): Telegram alias of the participant
        event_datetime (str): Event datetime formatted as string
        location (str): Event location
        is_online (bool): Whether event is online
    """
    if not user_alias:
        logger.warning("Missing telegram alias for reminder notification")
        return

    user_alias = user_alias.lstrip("@")

    import re

    if not re.match(r"^[a-zA-Z0-9_]+$", user_alias):
        logger.error(f"Invalid telegram alias format: {user_alias}")
        return

    location_text = "Online" if is_online else location
    message = f"⏰ Reminder: '{event_name}' starts in 12 hours!\n📅 Time: {event_datetime}\n📍 Location: {location_text}"

    try:
        encoded_event_name = quote(event_name, safe="")
        url = f"{BASE_URL}/notifyUser/{encoded_event_name}/{user_alias}/"
        payload = {"text": message}

        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        logger.info(
            f"Successfully sent reminder for event '{event_name}' to {user_alias}"
        )
    except Exception as e:
        logger.error(f"Failed to send reminder notification: {e!s}")


def notify_event_updated(event_name: str, user_alias: str, changes: dict):
    """
    Notify participant about event updates

    Args:
        event_name (str): Name of the event
        user_alias (str): Telegram alias of the participant
        changes (dict): Dictionary of changed fields and their new values
    """
    if not user_alias:
        logger.warning("Missing telegram alias for update notification")
        return

    user_alias = user_alias.lstrip("@")

    import re

    if not re.match(r"^[a-zA-Z0-9_]+$", user_alias):
        logger.error(f"Invalid telegram alias format: {user_alias}")
        return

    change_lines = []
    for field, new_value in changes.items():
        if field == "datetime":
            change_lines.append(f"📅 New time: {new_value}")
        elif field == "location":
            change_lines.append(f"📍 New location: {new_value}")
        elif field == "cost":
            change_lines.append(f"💵 New cost: ${new_value}")
        elif field == "is_online":
            status = "Online" if new_value else "In-person"
            change_lines.append(f"🌐 Format changed to: {status}")

    message = f"📝 Event '{event_name}' has been updated:\n" + "\n".join(change_lines)

    try:
        encoded_event_name = quote(event_name, safe="")
        url = f"{BASE_URL}/notifyUser/{encoded_event_name}/{user_alias}/"
        payload = {"text": message}

        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        logger.info(
            f"Successfully sent update notification for event '{event_name}' to {user_alias}"
        )
    except Exception as e:
        logger.error(f"Failed to send update notification: {e!s}")


def notify_event_deleted(event_name: str, user_alias: str, event_datetime: str):
    """
    Notify participant about event deletion

    Args:
        event_name (str): Name of the event
        user_alias (str): Telegram alias of the participant
        event_datetime (str): Original event datetime
    """
    if not user_alias:
        logger.warning("Missing telegram alias for deletion notification")
        return

    user_alias = user_alias.lstrip("@")

    import re

    if not re.match(r"^[a-zA-Z0-9_]+$", user_alias):
        logger.error(f"Invalid telegram alias format: {user_alias}")
        return

    message = (
        f"❌ Event '{event_name}' scheduled for {event_datetime} has been cancelled."
    )

    try:
        encoded_event_name = quote(event_name, safe="")
        url = f"{BASE_URL}/notifyUser/{encoded_event_name}/{user_alias}/"
        payload = {"text": message}

        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        logger.info(
            f"Successfully sent deletion notification for event '{event_name}' to {user_alias}"
        )
    except Exception as e:
        logger.error(f"Failed to send deletion notification: {e!s}")
