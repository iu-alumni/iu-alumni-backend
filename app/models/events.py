from sqlalchemy import Column, Float, String, DateTime, Boolean, ARRAY, ForeignKey
from app.core.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    owner_id = Column(String, ForeignKey('alumni.id'), nullable=False)
    participants_ids = Column(ARRAY(String), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    location = Column(String, nullable=False)
    datetime = Column(DateTime, nullable=False)
    cost = Column(Float, nullable=False)
    is_online = Column(Boolean, nullable=False)
    cover = Column(String, nullable=True)
    approved = Column(Boolean, nullable=True, default=None)