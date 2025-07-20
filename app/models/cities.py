from sqlalchemy import Column, Float, Index, String

from app.core.database import Base


class City(Base):
    __tablename__ = "cities"

    # Composite primary key on city + country since we don't have an id
    city = Column(String, primary_key=True, nullable=False)
    country = Column(String, primary_key=True, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    # Create indexes for better search performance
    __table_args__ = (
        Index("idx_city_name", "city"),
        Index("idx_country", "country"),
    )
