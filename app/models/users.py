from sqlalchemy import Boolean, Column, ForeignKey, DateTime, String, Table
from sqlalchemy.orm import relationship

from app.core.database import Base


alumni_follows = Table(
    "alumni_follows",
    Base.metadata,
    Column("follower_id", String, ForeignKey("alumni.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True),
    Column("followed_id", String, ForeignKey("alumni.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True),
)


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

    followers = relationship(
        "Alumni",
        secondary=alumni_follows,
        primaryjoin=id == alumni_follows.c.followed_id,
        secondaryjoin=id == alumni_follows.c.follower_id,
        back_populates="following",
        foreign_keys=[alumni_follows.c.followed_id, alumni_follows.c.follower_id],
    )

    following = relationship(
        "Alumni",
        secondary=alumni_follows,
        primaryjoin=id == alumni_follows.c.follower_id,
        secondaryjoin=id == alumni_follows.c.followed_id,
        back_populates="followers",
        foreign_keys=[alumni_follows.c.follower_id, alumni_follows.c.followed_id],
    )

    @property
    def followers_count(self) -> int:
        return len(self.followers) if self.followers is not None else 0

    @property
    def following_count(self) -> int:
        return len(self.following) if self.following is not None else 0


class Admin(Base):
    __tablename__ = "admins"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
