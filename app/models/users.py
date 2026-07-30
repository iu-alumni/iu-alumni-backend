from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.orm import relationship

from app.core.database import Base


# Kept in one place so the schema layer, the mobile app, and the admin
# portal all agree on the wire format.
ALUMNI_ROLE_ALUMNI = "alumni"
ALUMNI_ROLE_FRIEND = "alumni_friend"
ALUMNI_ROLES = (ALUMNI_ROLE_ALUMNI, ALUMNI_ROLE_FRIEND)


class Alumni(Base):
    __tablename__ = "alumni"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    # NULL for Alumni Friends (staff / dropouts / other non-graduates).
    graduation_year = Column(String, nullable=True)
    # 'alumni' by default. Alumni Friends can't set graduation_year and
    # render a chip instead of the year tag on their profile.
    role = Column(
        Enum(*ALUMNI_ROLES, name="alumni_role"),
        nullable=False,
        default=ALUMNI_ROLE_ALUMNI,
        server_default=ALUMNI_ROLE_ALUMNI,
    )
    location = Column(String)
    biography = Column(String)
    show_location = Column(Boolean, default=False)
    telegram_alias = Column(String)
    is_telegram_verified = Column(Boolean, default=False, nullable=False)
    avatar = Column(String)
    is_verified = Column(Boolean, default=False, index=True)
    is_banned = Column(Boolean, default=False, index=True)
    # Cursor for the notifications panel: an event is "unread" until this
    # is >= the moment the event entered the ~7-day notice window. See
    # app/services/notifications.py.
    notifications_seen_at = Column(DateTime, nullable=True)

    # Relationship
    email_verification = relationship(
        "EmailVerification", back_populates="alumni", uselist=False
    )


class Admin(Base):
    __tablename__ = "admins"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
