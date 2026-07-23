from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.profile import FollowStatusResponse

router = APIRouter()


@router.post("/{user_id}/follow", response_model=FollowStatusResponse)
def follow_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Alumni = Depends(get_current_user),
):
    if not isinstance(current_user, Alumni):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not an alumni account",
        )

    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users cannot follow themselves",
        )

    target_user = db.query(Alumni).filter(Alumni.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if target_user in current_user.following:
        return FollowStatusResponse(user_id=user_id, is_following=True)

    current_user.following.append(target_user)
    db.commit()
    db.refresh(current_user)

    return FollowStatusResponse(user_id=user_id, is_following=True)


@router.delete("/{user_id}/follow", response_model=FollowStatusResponse)
def unfollow_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Alumni = Depends(get_current_user),
):
    if not isinstance(current_user, Alumni):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not an alumni account",
        )

    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users cannot unfollow themselves",
        )

    target_user = db.query(Alumni).filter(Alumni.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if target_user in current_user.following:
        current_user.following.remove(target_user)
        db.commit()
        db.refresh(current_user)

    return FollowStatusResponse(user_id=user_id, is_following=False)


@router.get("/{user_id}/follow", response_model=FollowStatusResponse)
def get_follow_status(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Alumni = Depends(get_current_user),
):
    if not isinstance(current_user, Alumni):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not an alumni account",
        )

    if current_user.id == user_id:
        return FollowStatusResponse(user_id=user_id, is_following=False)

    target_user = db.query(Alumni).filter(Alumni.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return FollowStatusResponse(user_id=user_id, is_following=target_user in current_user.following)
