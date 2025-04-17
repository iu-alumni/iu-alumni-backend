from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.users import Alumni
from app.schemas.profile import ProfileResponse

router = APIRouter()

@router.get("/all", response_model=list[ProfileResponse])
def get_profiles(
    db: Session = Depends(get_db)
):
    """
    Get the list of all profiles.
    """
    print("PRE HELLO")
    users = db.query(Alumni).all()
    print("HELLO")
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users