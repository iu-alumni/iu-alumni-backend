import logging
import os
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr


# Get logger for this module
logger = logging.getLogger("iu_alumni.email_service")

_mail_username = os.getenv("MAIL_USERNAME", "")
_mail_password = os.getenv("MAIL_PASSWORD", "")

if not _mail_username or not _mail_password:
    logger.warning(
        "SMTP credentials are not configured (MAIL_USERNAME and/or MAIL_PASSWORD are empty). "
        "All email sends will fail. "
        "If using Gmail/Google Workspace, generate an App Password at "
        "myaccount.google.com -> Security -> 2-Step Verification -> App Passwords."
    )

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "email"

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=_mail_username,
    MAIL_PASSWORD=_mail_password,
    MAIL_FROM=os.getenv("MAIL_FROM", "noreply@innopolis.university"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "IU Alumni Platform"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=_TEMPLATES_DIR,
)

# Initialize FastMail instance
fm = FastMail(conf)


async def send_login_code_email(
    email: EmailStr, first_name: str, code: str, expiry_minutes: int = 10
) -> bool:
    """Send 2FA login code email."""
    try:
        message = MessageSchema(
            subject="IU Alumni — Your login code",
            recipients=[email],
            template_body={
                "first_name": first_name,
                "code": code,
                "expiry_minutes": expiry_minutes,
            },
            subtype=MessageType.html,
        )
        await fm.send_message(message, template_name="login_code.html")
        return True
    except Exception:
        logger.exception("Failed to send login code email to %s", email)
        return False


async def send_password_reset_email(
    email: EmailStr, first_name: str, reset_link: str, expiry_minutes: int = 30
) -> bool:
    """Send password reset link email."""
    try:
        message = MessageSchema(
            subject="IU Alumni — Reset your password",
            recipients=[email],
            template_body={
                "first_name": first_name,
                "reset_link": reset_link,
                "expiry_minutes": expiry_minutes,
            },
            subtype=MessageType.html,
        )
        await fm.send_message(message, template_name="password_reset.html")
        return True
    except Exception:
        logger.exception("Failed to send password reset email to %s", email)
        return False


async def send_verification_email(
    email: EmailStr, first_name: str, verification_code: str
) -> bool:
    """
    Send verification code email to user

    Args:
        email: User's email address
        first_name: User's first name
        verification_code: 6-digit verification code

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        message = MessageSchema(
            subject="Verify your IU Alumni account",
            recipients=[email],
            template_body={
                "first_name": first_name,
                "verification_code": verification_code,
            },
            subtype=MessageType.html,
        )
        logger.info("Sending verification email to %s", email)
        await fm.send_message(message, template_name="verification.html")
        return True
    except Exception:
        logger.exception("Failed to send verification email to %s", email)
        return False


async def send_manual_verification_notification(
    admin_email: EmailStr, user_email: str, user_name: str
) -> bool:
    """
    Send notification to admin about manual verification request

    Args:
        admin_email: Admin's email address
        user_email: User's email requesting verification
        user_name: User's full name

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        message = MessageSchema(
            subject="Manual Verification Request — IU Alumni",
            recipients=[admin_email],
            template_body={
                "user_name": user_name,
                "user_email": user_email,
            },
            subtype=MessageType.html,
        )
        await fm.send_message(message, template_name="manual_verification.html")
        return True
    except Exception:
        logger.exception("Failed to send admin notification to %s", admin_email)
        return False


async def send_verification_success_email(email: EmailStr, first_name: str) -> bool:
    """
    Send confirmation email after successful verification

    Args:
        email: User's email address
        first_name: User's first name

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        message = MessageSchema(
            subject="Account Verified — IU Alumni Platform",
            recipients=[email],
            template_body={"first_name": first_name},
            subtype=MessageType.html,
        )
        await fm.send_message(message, template_name="verification_success.html")
        return True
    except Exception:
        logger.exception("Failed to send verification success email to %s", email)
        return False


async def send_verification_link_email(
    email: EmailStr, first_name: str, verify_link: str, expiry_hours: int = 24
) -> bool:
    """Send link-based registration email verification."""
    try:
        message = MessageSchema(
            subject="Verify your IU Alumni account",
            recipients=[email],
            template_body={
                "first_name": first_name,
                "verify_link": verify_link,
                "expiry_hours": expiry_hours,
            },
            subtype=MessageType.html,
        )
        logger.info("Sending verification link email to %s", email)
        await fm.send_message(message, template_name="verification_link.html")
        return True
    except Exception:
        logger.exception("Failed to send verification link email to %s", email)
        return False


async def send_telegram_verification_email(
    email: EmailStr, first_name: str, telegram_alias: str, verify_link: str, expiry_hours: int = 24
) -> bool:
    """Send link-based Telegram account verification email."""
    try:
        message = MessageSchema(
            subject="Confirm your Telegram account — IU Alumni",
            recipients=[email],
            template_body={
                "first_name": first_name,
                "telegram_alias": telegram_alias.lstrip("@"),
                "verify_link": verify_link,
                "expiry_hours": expiry_hours,
            },
            subtype=MessageType.html,
        )
        logger.info("Sending Telegram verification email to %s", email)
        await fm.send_message(message, template_name="telegram_verification.html")
        return True
    except Exception:
        logger.exception("Failed to send Telegram verification email to %s", email)
        return False
