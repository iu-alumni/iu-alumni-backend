from sqlalchemy import Column, Float, String, DateTime, Boolean, ARRAY, ForeignKeyConstraint
from app.core.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    owner_id = Column(String, nullable=False)
    participants_ids = Column(ARRAY(String), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    location = Column(String, nullable=False)
    datetime = Column(DateTime, nullable=False)
    cost = Column(Float, nullable=False)
    is_online = Column(Boolean, nullable=False)
    cover = Column(String, nullable=True)
    
    # Define the foreign key relationships at the table level
    __table_args__ = (
        ForeignKeyConstraint(['owner_id'], ['alumni.id'], name='fk_event_alumni', ondelete='CASCADE'),
        ForeignKeyConstraint(['owner_id'], ['admins.id'], name='fk_event_admin', ondelete='CASCADE'),
    )