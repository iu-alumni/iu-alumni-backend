from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Union
from app.core.database import get_db
from app.models.users import Alumni, Admin
from app.core.security import get_current_user

router = APIRouter()

@router.post("/ban/{user_id}")
def ban_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Union[Admin, Alumni] = Depends(get_current_user)
):
    if not isinstance(current_user, Admin):
        raise HTTPException(status_code=403, detail="You are not authorized to ban users")
    user = db.query(Alumni).filter(Alumni.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_banned:
        raise HTTPException(status_code=400, detail="User is already banned")
    user.is_banned = True
    db.commit()
    db.refresh(user)
    return {"message": "User banned successfully"}