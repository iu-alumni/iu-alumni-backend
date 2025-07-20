from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(JSONB, nullable=False)
