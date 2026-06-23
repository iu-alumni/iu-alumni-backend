from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Badge(Base):
    __tablename__ = "badges"

    id = Column(String, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    tier = Column(String, nullable=False)  # gold|silver|bronze|special
    icon_key = Column(String, nullable=False)
    strategy = Column(String, nullable=False)
    params = Column(JSONB, nullable=False, default=dict)
    trigger_metrics = Column(ARRAY(String), nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    awards = relationship("UserBadge", back_populates="badge")


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (
        UniqueConstraint(
            "alumni_id", "badge_id", "extra", name="uq_user_badges_unique"
        ),
    )

    id = Column(String, primary_key=True)
    alumni_id = Column(
        String, ForeignKey("alumni.id", ondelete="CASCADE"), nullable=False, index=True
    )
    badge_id = Column(String, ForeignKey("badges.id", ondelete="CASCADE"), nullable=False)
    awarded_at = Column(DateTime, nullable=False, server_default=func.now())
    seen_at = Column(DateTime, nullable=True)
    extra = Column(JSONB, nullable=False, default=dict)  # e.g. {"city": "...", "year": ...}
    awarded_by = Column(String, nullable=True)

    badge = relationship("Badge", back_populates="awards")
