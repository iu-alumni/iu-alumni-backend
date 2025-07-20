from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.auth import AdminVerifyRequest
from app.services.email_service import send_verification_success_email
from app.services.verification_service import admin_verify_user


router = APIRouter()


@router.post("/verify")
async def verify_user(
    request: AdminVerifyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """
    Admin endpoint to manually verify a user
    """
    # Check if current user is admin
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to verify users",
        )

    # Verify the user
    success, message = admin_verify_user(db, request.email)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Get the verified user to send email
    user = db.query(Alumni).filter(Alumni.email == request.email).first()
    if user:
        background_tasks.add_task(
            send_verification_success_email, user.email, user.first_name
        )

    return {"message": message, "email": request.email}
