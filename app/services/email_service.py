import logging
import os

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
)

# Initialize FastMail instance
fm = FastMail(conf)


async def send_login_code_email(
    email: EmailStr, first_name: str, code: str, expiry_minutes: int = 10
) -> bool:
    """Send 2FA login code email."""
    try:
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">IU Alumni — Login Verification</h2>
                    <p>Hi {first_name},</p>
                    <p>Use the code below to complete your login. It expires in {expiry_minutes} minutes.</p>
                    <div style="background-color: #f4f4f4; padding: 20px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #0066cc; letter-spacing: 5px; margin: 0;">{code}</h1>
                    </div>
                    <p>If you didn't attempt to log in, please ignore this email.</p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        This is an automated message from IU Alumni Platform.
                        Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """
        message = MessageSchema(
            subject="IU Alumni — Your login code",
            recipients=[email],
            body=body,
            subtype=MessageType.html,
        )
        await fm.send_message(message)
        return True
    except Exception:
        logger.exception("Failed to send login code email to %s", email)
        return False


async def send_password_reset_email(
    email: EmailStr, first_name: str, reset_link: str, expiry_minutes: int = 30
) -> bool:
    """Send password reset link email."""
    try:
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">Password Reset Request</h2>
                    <p>Hi {first_name},</p>
                    <p>We received a request to reset your IU Alumni Platform password.
                    Click the button below to set a new password. This link expires in {expiry_minutes} minutes.</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}"
                           style="background-color: #0066cc; color: white; padding: 12px 30px;
                                  text-decoration: none; border-radius: 4px; font-size: 16px;">
                            Reset Password
                        </a>
                    </div>
                    <p>Or copy this link into your browser:</p>
                    <p style="word-break: break-all; color: #0066cc;">{reset_link}</p>
                    <p>If you didn't request a password reset, please ignore this email.
                    Your password will not be changed.</p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        This is an automated message from IU Alumni Platform.
                        Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """
        message = MessageSchema(
            subject="IU Alumni — Reset your password",
            recipients=[email],
            body=body,
            subtype=MessageType.html,
        )
        await fm.send_message(message)
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
        # Create email body
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">Welcome to IU Alumni Platform!</h2>

                    <p>Hi {first_name},</p>

                    <p>Thank you for registering with the IU Alumni Platform. To complete your registration,
                    please use the verification code below:</p>

                    <div style="background-color: #f4f4f4; padding: 20px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #0066cc; letter-spacing: 5px; margin: 0;">{verification_code}</h1>
                    </div>

                    <p>This code will expire in 1 hour for security purposes.</p>

                    <p>If you didn't request this verification, please ignore this email.</p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                    <p style="font-size: 12px; color: #666;">
                        This is an automated message from IU Alumni Platform.
                        Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """

        message = MessageSchema(
            subject="Verify your IU Alumni account",
            recipients=[email],
            body=body,
            subtype=MessageType.html,
        )

        logger.info(f"Sending verification email to {email}")
        await fm.send_message(message)
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
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">Manual Verification Request</h2>

                    <p>A new user has requested manual verification:</p>

                    <div style="background-color: #f4f4f4; padding: 20px; margin: 20px 0;">
                        <p><strong>Name:</strong> {user_name}</p>
                        <p><strong>Email:</strong> {user_email}</p>
                    </div>

                    <p>Please review and verify this user in the admin panel.</p>
                </div>
            </body>
        </html>
        """

        message = MessageSchema(
            subject="Manual Verification Request - IU Alumni",
            recipients=[admin_email],
            body=body,
            subtype=MessageType.html,
        )

        await fm.send_message(message)
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
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">Welcome to IU Alumni Platform!</h2>

                    <p>Hi {first_name},</p>

                    <p>Your account has been successfully verified! You can now log in to the IU Alumni Platform
                    and start connecting with fellow alumni.</p>

                    <p>We're excited to have you as part of our community!</p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                    <p style="font-size: 12px; color: #666;">
                        This is an automated message from IU Alumni Platform.
                        Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """

        message = MessageSchema(
            subject="Account Verified - IU Alumni Platform",
            recipients=[email],
            body=body,
            subtype=MessageType.html,
        )

        await fm.send_message(message)
        return True

    except Exception:
        logger.exception("Failed to send verification success email to %s", email)
        return False
