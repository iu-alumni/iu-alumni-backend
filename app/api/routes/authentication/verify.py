from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.models.users import Alumni
from app.schemas.auth import TokenResponse, VerifyEmailRequest
from app.services.email_service import send_verification_success_email
from app.services.verification_service import verify_code


router = APIRouter()


@router.post("/verify", response_model=TokenResponse)
async def verify_email(
    request: VerifyEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Verify email with verification code and return access token
    """
    # Verify the code
    success, message = verify_code(db, request.email, request.verification_code)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Get the verified user
    user = db.query(Alumni).filter(Alumni.email == request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Send success email
    background_tasks.add_task(
        send_verification_success_email, user.email, user.first_name
    )

    # Generate access token
    user_data = {"sub": user.email, "user_id": user.id, "user_type": "alumni"}
    access_token = create_access_token(data=user_data)

    return {"access_token": access_token, "token_type": "bearer"}
