from sqlalchemy import Boolean, Column, String, Enum, Integer
from app.core.database import Base
from app.models.enums import GraduationCourse

class Alumni(Base):
    __tablename__ = "alumni"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    graduation_year = Column(Integer)
    course = Column(Enum(GraduationCourse))
    location = Column(String, nullable=True)
    biography = Column(String, nullable=True)
    show_location = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)

class Admin(Base):
    __tablename__ = "admins"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
