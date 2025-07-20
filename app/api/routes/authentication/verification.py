from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash
from app.models.users import Alumni
from app.schemas.auth import TokenResponse, VerifyGraduateRequest


router = APIRouter()


@router.post("/verify-graduate", response_model=TokenResponse)
def verify_graduate(request: VerifyGraduateRequest, db: Session = Depends(get_db)):
    """Verify graduate identity and set password."""
    user = db.query(Alumni).filter(Alumni.email == request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified"
        )

    # Verify graduation year and first name
    if (
        user.graduation_year != request.graduation_year
        or user.first_name.lower() != request.first_name.lower()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification information",
        )

    # Update user data
    user.hashed_password = get_password_hash(request.password)
    user.is_verified = True

    db.commit()

    # Generate access token with consistent data structure
    user_data = {"sub": user.email, "user_id": user.id, "user_type": "alumni"}
    access_token = create_access_token(data=user_data)

    return {"access_token": access_token, "token_type": "bearer"}
