from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List
import os
from pathlib import Path

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM=os.getenv("MAIL_FROM", "noreply@innopolis.university"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "IU Alumni Platform"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates" / "email"
)

# Initialize FastMail instance
fm = FastMail(conf)

async def send_verification_email(
    email: EmailStr,
    first_name: str,
    verification_code: str
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
            subtype=MessageType.html
        )
        
        try:
            print(f"Sending verification email to {email}")
            await fm.send_message(message)
            return True
        except Exception as e:
            print(f"Failed to send verification email: {str(e)}")
            return False
        
    except Exception as e:
        print(f"Failed to send verification email: {str(e)}")
        return False

async def send_manual_verification_notification(
    admin_email: EmailStr,
    user_email: str,
    user_name: str
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
            subtype=MessageType.html
        )
        
        await fm.send_message(message)
        return True
        
    except Exception as e:
        print(f"Failed to send admin notification: {str(e)}")
        return False

async def send_verification_success_email(
    email: EmailStr,
    first_name: str
) -> bool:
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
            subtype=MessageType.html
        )
        
        await fm.send_message(message)
        return True
        
    except Exception as e:
        print(f"Failed to send verification success email: {str(e)}")
        return False