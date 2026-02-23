#!/usr/bin/env python3
"""
Script to send 12-hour reminders for upcoming events.
Run this script hourly via cron to check for events starting in 12 hours.

Example crontab entry:
0 * * * * cd /path/to/iu-alumni-backend && source venv/bin/activate && python scripts/send_event_reminders.py
"""

from datetime import datetime, timedelta
import logging
import os
import sys


# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes.utils.notifications import notify_event_reminder
from app.models.events import Event
from app.models.users import Alumni


# Load environment variables
load_dotenv(override=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_session():
    """Create a database session"""
    database_url = os.getenv("SQLALCHEMY_DATABASE_URL")
    if not database_url:
        raise ValueError("SQLALCHEMY_DATABASE_URL environment variable is not set")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def send_reminders():
    """Check for events starting in 12 hours and send reminders"""
    db = get_db_session()

    try:
        # Calculate the time window (12 hours from now, +/- 30 minutes)
        now = datetime.utcnow()
        reminder_time = now + timedelta(hours=12)
        time_window_start = reminder_time - timedelta(minutes=30)
        time_window_end = reminder_time + timedelta(minutes=30)

        logger.info(
            f"Checking for events between {time_window_start} and {time_window_end}"
        )

        # Query events that:
        # 1. Are approved
        # 2. Start within the 12-hour window
        # 3. Have participants
        events = (
            db.query(Event)
            .filter(
                Event.approved == True,
                Event.datetime >= time_window_start,
                Event.datetime <= time_window_end,
            )
            .all()
        )

        logger.info(f"Found {len(events)} events to send reminders for")

        for event in events:
            # Get event owner
            owner = db.query(Alumni).filter(Alumni.id == event.owner_id).first()

            # Get all users to notify (participants + owner)
            users_to_notify = (
                set(event.participants_ids) if event.participants_ids else set()
            )
            if owner:
                users_to_notify.add(owner.id)

            if not users_to_notify:
                logger.info(f"Event '{event.title}' has no users to notify, skipping")
                continue

            logger.info(
                f"Processing reminders for event '{event.title}' with {len(users_to_notify)} users"
            )

            # Send reminder to each user
            for user_id in users_to_notify:
                user = db.query(Alumni).filter(Alumni.id == user_id).first()

                if not user:
                    logger.warning(f"User {user_id} not found")
                    continue

                if not user.telegram_alias:
                    logger.info(
                        f"User {user.first_name} {user.last_name} has no telegram alias"
                    )
                    continue

                # Format datetime for display
                event_datetime_str = event.datetime.strftime("%Y-%m-%d %H:%M UTC")

                # Send the reminder
                notify_event_reminder(
                    event_name=event.title,
                    user_alias=user.telegram_alias,
                    event_datetime=event_datetime_str,
                    location=event.location,
                    is_online=event.is_online,
                )

                logger.info(
                    f"Sent reminder to {user.telegram_alias} for event '{event.title}'"
                )

        logger.info("Reminder sending completed")

    except Exception as e:
        logger.error(f"Error sending reminders: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting event reminder script")
    send_reminders()
    logger.info("Event reminder script finished")
