from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class AllowedEmail(Base):
    __tablename__ = "allowed_emails"

    id = Column(String, primary_key=True)
    hashed_email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())