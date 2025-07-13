from datetime import datetime, timedelta, UTC
import secrets
from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.users import Alumni, Admin
from jose.exceptions import JWTError
import os

# Configure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 366 # 1 year

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Use HTTPBearer for token extraction
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify if the provided password matches the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a hashed version of the password."""
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def get_random_token() -> str:
    """Generate a random token for user IDs, verification tokens, etc."""
    import uuid
    return str(uuid.uuid4())

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get the current user from the JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    if user_type == "alumni":
        user = db.query(Alumni).filter(Alumni.email == email).first()
    elif user_type == "admin":
        user = db.query(Admin).filter(Admin.email == email).first()
    else:
        raise credentials_exception
    
    if user is None:
        raise credentials_exception
    
    return user 