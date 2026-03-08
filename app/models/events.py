from sqlalchemy import ARRAY, Boolean, Column, DateTime, Float, ForeignKey, Index, String

from app.core.database import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_approved_datetime", "approved", "datetime"),
    )

    id = Column(String, primary_key=True)
    owner_id = Column(String, ForeignKey("alumni.id"), nullable=False, index=True)
    participants_ids = Column(ARRAY(String), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    location = Column(String, nullable=False)
    datetime = Column(DateTime, nullable=False, index=True)
    cost = Column(Float, nullable=False)
    is_online = Column(Boolean, nullable=False)
    cover = Column(String, nullable=True)
    approved = Column(Boolean, nullable=True, default=None, index=True)
