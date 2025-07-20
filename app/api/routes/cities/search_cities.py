from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.cities import City
from app.models.users import Admin, Alumni
from app.schemas.city import CityLocation, CitySearchResponse, Coordinates


router = APIRouter()


@router.get("/coordinates", response_model=Coordinates | None)
async def get_coordinates(
    city: str = Query(..., description="City name"),
    country: str = Query(..., description="Country name"),
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """
    Get coordinates (lat/lng) for a specific city and country.

    Returns null if the city/country combination is not found.

    Matches the Dart coordinates() method functionality.
    """
    result = (
        db.query(City.lat, City.lng)
        .filter(
            and_(
                func.lower(City.city) == city.lower(),
                func.lower(City.country) == country.lower(),
            )
        )
        .first()
    )

    if not result:
        return None

    return Coordinates(lat=result.lat, lng=result.lng)


@router.get("/search", response_model=CitySearchResponse)
async def search_cities(
    q: str = Query(..., description="Search query for city name", min_length=1),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """
    Search for cities by partial name match.

    Returns up to 10 cities matching the search query.

    Matches the Dart cities() method functionality with FTS-like behavior.
    """
    search_term = q.strip()

    if not search_term:
        return CitySearchResponse(cities=[])

    # Use PostgreSQL pattern matching for prefix search (like FTS MATCH with wildcard)
    # This mimics the SQLite FTS 'city MATCH ? || "*"' behavior
    cities = (
        db.query(City.city, City.country, City.lat, City.lng)
        .filter(func.lower(City.city).like(func.lower(f"{search_term}%")))
        .limit(limit)
        .all()
    )

    # Convert results to CityLocation objects
    city_locations = [
        CityLocation(city=city, country=country, lat=lat, lng=lng)
        for city, country, lat, lng in cities
    ]

    return CitySearchResponse(cities=city_locations)
