from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.email_verification import EmailVerification
from app.models.events import Event
from app.models.login_code import LoginCode
from app.models.password_reset_token import PasswordResetToken
from app.models.projects import Project
from app.models.telegram_verify_token import TelegramVerifyToken
from app.models.users import Admin, Alumni


router = APIRouter()


@router.delete("/alumni/{alumni_id}")
def delete_alumni(
    alumni_id: str,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Permanently delete an alumnus and everything referencing them.

    `user_badges` cascades at the DB level already; every other table with
    an `alumni_id`/`owner_id` foreign key does not, so those rows are
    removed explicitly here, in the order that avoids constraint
    violations (owned content first, then auth-flow rows, then the alumni
    itself). `participants_ids`/`contributors_ids` aren't real foreign
    keys, so this alumnus's id is also stripped from other people's
    events/projects rather than left dangling in those arrays.
    """
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=403, detail="You are not authorized to delete users"
        )

    alumni = db.query(Alumni).filter(Alumni.id == alumni_id).first()
    if not alumni:
        raise HTTPException(status_code=404, detail="User not found")

    db.query(Event).filter(Event.owner_id == alumni_id).delete(synchronize_session=False)
    db.query(Project).filter(Project.owner_id == alumni_id).delete(synchronize_session=False)

    db.query(EmailVerification).filter(
        EmailVerification.alumni_id == alumni_id
    ).delete(synchronize_session=False)
    db.query(LoginCode).filter(LoginCode.alumni_id == alumni_id).delete(
        synchronize_session=False
    )
    db.query(PasswordResetToken).filter(
        PasswordResetToken.alumni_id == alumni_id
    ).delete(synchronize_session=False)
    db.query(TelegramVerifyToken).filter(
        TelegramVerifyToken.alumni_id == alumni_id
    ).delete(synchronize_session=False)

    # Filtered in Python, not `.any(alumni_id)` at the SQL level — confirmed
    # locally that comparator isn't portable to every backend this query
    # could run against, and a plain scan is simple enough for these tables.
    for event in db.query(Event).all():
        if alumni_id in event.participants_ids:
            event.participants_ids = [pid for pid in event.participants_ids if pid != alumni_id]

    for project in db.query(Project).all():
        if alumni_id in project.contributors_ids:
            project.contributors_ids = [
                pid for pid in project.contributors_ids if pid != alumni_id
            ]

    db.delete(alumni)
    db.commit()

    return {"message": "User deleted successfully"}
