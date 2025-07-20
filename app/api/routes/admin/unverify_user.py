from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.auth import AdminVerifyRequest
from app.services.verification_service import admin_unverify_user


router = APIRouter()


@router.post("/unverify")
async def unverify_user(
    request: AdminVerifyRequest,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """
    Admin endpoint to unverify a user
    """
    # Check if current user is admin
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to unverify users",
        )

    # Unverify the user
    success, message = admin_unverify_user(db, request.email)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return {"message": message, "email": request.email}
