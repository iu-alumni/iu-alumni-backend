from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Union

from app.core.database import get_db
from app.core.security import get_password_hash, get_random_token, get_current_user
from app.models.users import Admin, Alumni
from app.schemas.auth import AdminCreateRequest

router = APIRouter()

@router.post("/add-admin", status_code=status.HTTP_201_CREATED)
def add_admin(
    request: AdminCreateRequest,
    db: Session = Depends(get_db),
    current_user: Union[Admin, Alumni] = Depends(get_current_user)
):
    """
    Add a new admin user. Only existing admins can add new admins.
    """
    # Check if the current user is an admin
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add new admin users"
        )
    
    # Check if an admin with this email already exists
    existing_admin = db.query(Admin).filter(Admin.email == request.email).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An admin with this email already exists"
        )
    
    # Create new admin user
    new_admin = Admin(
        id=get_random_token(),
        email=request.email,
        hashed_password=get_password_hash(request.password)
    )
    
    # Add to database and commit
    db.add(new_admin)
    db.commit()
    
    return {"message": "Admin created successfully", "email": request.email}
