import hashlib
import hmac
import logging
import os

import pandas as pd
from sqlalchemy.orm import Session

from app.core.security import get_random_token
from app.models.allowed_emails import AllowedEmail


# Get logger for this module
logger = logging.getLogger("iu_alumni.email_hash_service")

# Get secret key from environment
EMAIL_HASH_SECRET = os.getenv("EMAIL_HASH_SECRET")


def _check_email_hash_secret():
    """Check if EMAIL_HASH_SECRET is configured."""
    if not EMAIL_HASH_SECRET:
        logger.warning("EMAIL_HASH_SECRET environment variable is not configured")
        return False
    return True


def hash_email(email: str) -> str:
    """Hash an email address using HMAC and SHA-256."""
    if not _check_email_hash_secret():
        raise ValueError("EMAIL_HASH_SECRET not configured")

    # Normalize email
    normalized_email = email.lower().strip()

    logger.debug("Processing email hash request")

    # Create HMAC using SHA-256
    digest = hmac.new(
        EMAIL_HASH_SECRET.encode("utf-8"),
        normalized_email.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    logger.debug("Email hash generated successfully")

    return digest


def is_email_allowed(db: Session, email: str) -> bool:
    """Check if an email is in the allowed list."""
    # If EMAIL_HASH_SECRET is not configured, return False (email not allowed)
    if not _check_email_hash_secret():
        logger.warning(
            "EMAIL_HASH_SECRET not configured - treating email as not allowed"
        )
        return False

    try:
        logger.debug("Checking if email is in allowed list")
        hashed_email = hash_email(email)

        # Check if hashed email exists in allowed emails
        result = (
            db.query(AllowedEmail)
            .filter(AllowedEmail.hashed_email == hashed_email)
            .first()
            is not None
        )
        logger.info(f"Email allowed status: {result}")

        return result
    except Exception as e:
        logger.error(f"Error checking if email is allowed: {e!s}")
        return False


def process_excel_file(db: Session, file_content: bytes) -> dict:
    """Process an Excel file containing email addresses."""
    if not _check_email_hash_secret():
        return {
            "success": False,
            "message": "EMAIL_HASH_SECRET not configured",
        }

    try:
        logger.info(
            f"Starting to process Excel file, content size: {len(file_content)} bytes"
        )

        # Read Excel file
        emails_df = pd.read_excel(file_content)

        logger.info(f"Excel file loaded, shape: {emails_df.shape}")

        # Check if the dataframe has at least one column
        if emails_df.shape[1] < 1:
            logger.error("Excel file has no columns")
            return {
                "success": False,
                "message": "Excel file appears to be empty or has no columns",
            }

        # Get the first column, which should contain emails
        emails = emails_df.iloc[:, 0].tolist()
        logger.info(f"Extracted {len(emails)} email entries from first column")

        # Filter out any non-string values or empty strings
        emails = [
            str(email).strip() for email in emails if email and str(email).strip()
        ]
        logger.info(f"After filtering, {len(emails)} valid emails remain")

        # Hash and store emails
        added_count = 0
        for email in emails:
            logger.debug("Processing email entry")
            hashed_email = hash_email(email)

            # Check if this hashed email already exists
            existing = (
                db.query(AllowedEmail)
                .filter(AllowedEmail.hashed_email == hashed_email)
                .first()
            )
            if not existing:
                logger.debug("Adding new allowed email")
                new_allowed_email = AllowedEmail(
                    id=get_random_token(), hashed_email=hashed_email
                )
                db.add(new_allowed_email)
                added_count += 1
            else:
                logger.debug("Email already exists in allowed list")

        db.commit()
        logger.info(
            f"Commit successful. Added {added_count} new entries out of {len(emails)} total"
        )

        return {
            "success": True,
            "message": f"Successfully processed {len(emails)} emails. Added {added_count} new entries.",
        }
    except Exception as e:
        logger.error(f"Error processing file: {e!s}")
        db.rollback()
        return {"success": False, "message": f"Error processing file: {e!s}"}
