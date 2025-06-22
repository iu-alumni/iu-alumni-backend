import requests
import os
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("NOTIFICATION_BOT_URL", "https://alumap-notification-bot.netlify.app/.netlify/functions")
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
        logger.warning(f"Missing telegram alias for notification: owner={owner_alias}, user={user_alias}")
        return
        
    try:
        url = f"{BASE_URL}/notifyJoin/{event_name}/{owner_alias}/{user_alias}/"
        response = requests.post(url, timeout=TIMEOUT)
        response.raise_for_status()
        logger.info(f"Successfully sent join notification for event '{event_name}'")
    except Exception as e:
        logger.error(f"Failed to send join notification: {str(e)}")
        # Don't raise exception to avoid breaking the main flow if notification fails

def notify_admin_manual_verification(user_email: str, user_name: str, 
                                   graduation_year: str, telegram_alias: str = None):
    """
    Notify admins about manual verification request via Telegram
    
    Args:
        user_email (str): Email of the user requesting verification
        user_name (str): Full name of the user
        graduation_year (str): Graduation year
        telegram_alias (str): Optional telegram alias of the user
    """
    message = f"""🔔 Manual Verification Request

Name: {user_name}
Email: {user_email}
Graduation Year: {graduation_year}
Telegram: @{telegram_alias if telegram_alias else 'Not provided'}

To verify this user:
POST /admin/verify
{{"email": "{user_email}"}}"""
    
    try:
        url = f"{BASE_URL}/notifyAdmins"
        data = {"s": message}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=data, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        logger.info(f"Successfully sent manual verification notification for {user_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send admin notification: {str(e)}")
        return False

