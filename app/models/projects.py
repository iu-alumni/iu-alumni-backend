from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.sql import func

from app.core.database import Base


class Project(Base):
    """Alumni-proposed project.

    Follows the events pattern:
    - `approved` is tri-state (None = pending admin review, True = public,
      False = declined).
    - Editing an approved project resets `approved` to None so the change
      goes through review again — enforced at the route layer, not here.
    - `contributors_ids` is a Postgres ARRAY (rewritten to JSON in tests).
    """

    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_approved_created_at", "approved", "created_at"),
    )

    id = Column(String, primary_key=True)
    owner_id = Column(
        String, ForeignKey("alumni.id"), nullable=False, index=True
    )
    contributors_ids = Column(ARRAY(String), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    cover = Column(String, nullable=True)
    # Optional payment link (bank / Tinkoff / YooKassa / etc.). Free-text
    # so we don't tie ourselves to a specific provider — the client just
    # opens whatever URL the owner supplies.
    donation_link = Column(String, nullable=True)
    approved = Column(Boolean, nullable=True, default=None, index=True)
    created_at = Column(
        DateTime, nullable=False, server_default=func.now()
    )
