from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(String, primary_key=True)
    alumni_id = Column(String, ForeignKey("alumni.id"), unique=True, nullable=False)
    verification_code = Column(String, nullable=False)
    verification_code_expires = Column(DateTime, nullable=False)
    verification_requested_at = Column(DateTime, nullable=False)
    manual_verification_requested = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)

    # Relationship - using string reference to avoid circular imports
    alumni = relationship("Alumni", back_populates="email_verification")
