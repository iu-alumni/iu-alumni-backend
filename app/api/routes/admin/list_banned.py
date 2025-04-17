from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Union, List
from app.core.database import get_db
from app.models.users import Alumni, Admin
from app.core.security import get_current_user
from app.schemas.user import Alumni as AlumniSchema

router = APIRouter()

@router.get("/banned", response_model=List[AlumniSchema])
def list_banned(
    db: Session = Depends(get_db),
    current_user: Union[Admin, Alumni] = Depends(get_current_user)
):
    if not isinstance(current_user, Admin):
        raise HTTPException(status_code=403, detail="You are not authorized to list banned users")
    banned_users = db.query(Alumni).filter(Alumni.is_banned).all()
    return banned_users