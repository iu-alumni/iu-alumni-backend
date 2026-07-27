from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Alumni(Base):
    __tablename__ = "alumni"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    graduation_year = Column(String, nullable=False)
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
