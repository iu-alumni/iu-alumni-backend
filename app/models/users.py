from sqlalchemy import Boolean, Column, String, Enum, Integer
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
    avatar = Column(String)
    is_verified = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    
    # Relationship
    email_verification = relationship("EmailVerification", back_populates="alumni", uselist=False)

class Admin(Base):
    __tablename__ = "admins"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
