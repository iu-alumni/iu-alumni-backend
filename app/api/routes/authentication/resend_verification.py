from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.users import Alumni
from app.schemas.auth import ResendVerificationRequest
from app.services.email_service import send_verification_email
from app.services.verification_service import (
    can_resend_verification,
    create_verification_record,
)


router = APIRouter()


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification_code(
    request: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Resend verification code to user's email

    Rate limited to once per 60 seconds
    """
    # Check if user can request a new code
    can_resend, message, _alumni_id = can_resend_verification(db, request.email)

    if not can_resend:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Get user details
    user = db.query(Alumni).filter(Alumni.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Create/update verification record with new code
    verification = create_verification_record(
        db=db, alumni_id=user.id, manual_verification=False
    )

    # Send new verification email
    background_tasks.add_task(
        send_verification_email,
        user.email,
        user.first_name,
        verification.verification_code,
    )

    return {"message": "New verification code sent to your email", "email": user.email}
