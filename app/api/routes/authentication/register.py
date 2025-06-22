from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash, get_random_token
from app.models.users import Alumni, Admin
from app.schemas.auth import RegisterRequest
from app.services.email_service import send_verification_email, send_manual_verification_notification
from app.services.verification_service import create_verification_record
from app.api.routes.utils.notifications import notify_admin_manual_verification
import os

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register a new alumni user with email verification
    """
    # Check if email already exists
    existing_user = db.query(Alumni).filter(Alumni.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new alumni user (unverified)
    new_user = Alumni(
        id=get_random_token(),
        email=request.email,
        hashed_password=get_password_hash(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        graduation_year=request.graduation_year,
        telegram_alias=request.telegram_alias,
        is_verified=False,
        is_banned=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create verification record
    print(f"Creating verification record for {new_user.email}")
    verification = create_verification_record(
        db=db,
        alumni_id=new_user.id,
        manual_verification=request.manual_verification
    )
    print(f"Verification record created: {verification}")
    if request.manual_verification:
        # Send Telegram notification to admins
        background_tasks.add_task(
            notify_admin_manual_verification,
            new_user.email,
            f"{new_user.first_name} {new_user.last_name}",
            new_user.graduation_year,
            new_user.telegram_alias
        )
        
        # Also send email notifications to admins as backup
        admins = db.query(Admin).all()
        for admin in admins:
            background_tasks.add_task(
                send_manual_verification_notification,
                admin.email,
                new_user.email,
                f"{new_user.first_name} {new_user.last_name}"
            )
        
        return {
            "message": "Registration successful. Your account is pending manual verification by an administrator.",
            "email": new_user.email
        }
    else:
        # Send verification email
        print(f"Sending verification email to {new_user.email}")
        await send_verification_email(
            new_user.email,
            new_user.first_name,
            verification.verification_code
        )
        print(f"Verification email sent to {new_user.email}")
        return {
            "message": "Registration successful. Please check your email for verification code.",
            "email": new_user.email
        }