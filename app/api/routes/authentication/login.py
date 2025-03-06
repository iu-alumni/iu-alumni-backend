from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.users import Alumni, Admin
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and return a JWT token.
    """
    # Check alumni users first
    user = db.query(Alumni).filter(Alumni.email == request.email).first()
    
    # If not found in alumni, check admin users
    if not user:
        user = db.query(Admin).filter(Admin.email == request.email).first()
    
    # If user not found or password doesn't match
    if not user or not user.hashed_password or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if alumni user is verified
    if hasattr(user, 'is_verified') and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not verified"
        )
    
    # Check if alumni user is banned
    if hasattr(user, 'is_banned') and user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is banned"
        )
    
    # Create access token
    user_data = {
        "sub": user.email,
        "user_id": user.id,
        "user_type": "alumni" if isinstance(user, Alumni) else "admin"
    }
    
    access_token = create_access_token(data=user_data)
    
    return {"access_token": access_token, "token_type": "bearer"} 