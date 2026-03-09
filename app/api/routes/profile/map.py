from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.cities import City
from app.models.users import Admin, Alumni
from app.schemas.profile import MapLocationsResponse, MapLocationGroup


router = APIRouter()


@router.get("/map", response_model=MapLocationsResponse)
def get_map_locations(
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """
    Return alumni counts grouped by location for map pin display.

    Only alumni with ``show_location=True`` and a resolvable city/country are
    included. Coordinates come from a JOIN with the cities table so the mobile
    client does not need to make one round-trip per city to look up lat/lng.

    The location string is stored as ``"Country, City"`` (comma-space separated).
    We split it with PostgreSQL's ``split_part()`` function to join against the
    cities table, which is indexed on (city, country).

    Indexes used:
    - ``ix_alumni_show_location_location`` composite B-tree (leading filter)
    - ``idx_city_name`` / ``idx_country`` B-tree on cities table (JOIN condition)
    """
    country_expr = func.split_part(Alumni.location, ', ', 1)
    city_expr = func.split_part(Alumni.location, ', ', 2)

    rows = (
        db.query(
            country_expr.label('country'),
            city_expr.label('city'),
            City.lat,
            City.lng,
            func.count(Alumni.id).label('count'),
        )
        .join(
            City,
            (func.lower(city_expr) == func.lower(City.city))
            & (func.lower(country_expr) == func.lower(City.country)),
        )
        .filter(
            Alumni.show_location.is_(True),
            Alumni.location.isnot(None),
            Alumni.location.like('%, %'),
            Alumni.is_verified.is_(True),
            Alumni.is_banned.is_(False),
        )
        .group_by(country_expr, city_expr, City.lat, City.lng)
        .all()
    )

    locations = [
        MapLocationGroup(
            country=row.country,
            city=row.city,
            lat=row.lat,
            lng=row.lng,
            count=row.count,
        )
        for row in rows
    ]
    return MapLocationsResponse(locations=locations)
