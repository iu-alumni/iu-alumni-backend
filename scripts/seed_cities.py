"""Seed the `cities` table with reference city/country/lat/lng data.

The table has an Alembic migration that creates it, but nothing populates
it — `/cities/search` and `/cities/coordinates` return nothing until this
runs. Source data: a world-cities dataset bundled at scripts/data/worldcities.csv
(plus a couple of entries the dataset is missing but the platform needs).

Idempotent: safe to re-run. Only inserts (city, country) pairs not already
present in the table.

Run with:
    docker exec iu_alumni_backend python -m scripts.seed_cities
"""
from __future__ import annotations

import csv
from pathlib import Path

from app.core.database import SessionLocal
from app.models.cities import City


CSV_PATH = Path(__file__).parent / "data" / "worldcities.csv"

# (city, country, lat, lng) — added regardless of whether the CSV has them.
EXTRA_CITIES = [
    ("Innopolis", "Russia", 55.752117, 48.744552),
]


def _load_rows(csv_path: Path) -> list[tuple[str, str, float, float]]:
    """Read csv_path into deduped (city, country, lat, lng) tuples.

    Dedupes on (city, country) since that's the table's primary key —
    keeps the first occurrence found.
    """
    seen: set[tuple[str, str]] = set()
    rows: list[tuple[str, str, float, float]] = []

    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["city"], row["country"])
            if key in seen:
                continue
            try:
                lat, lng = float(row["lat"]), float(row["lng"])
            except (KeyError, ValueError):
                continue
            seen.add(key)
            rows.append((row["city"], row["country"], lat, lng))

    for city, country, lat, lng in EXTRA_CITIES:
        if (city, country) not in seen:
            seen.add((city, country))
            rows.append((city, country, lat, lng))

    return rows


def seed_cities(db, csv_path: Path = CSV_PATH) -> int:
    """Insert any (city, country) pairs from csv_path missing from the table.

    Returns the number of rows inserted.
    """
    rows = _load_rows(csv_path)

    existing = {(city, country) for city, country in db.query(City.city, City.country)}
    new_rows = [
        {"city": city, "country": country, "lat": lat, "lng": lng}
        for city, country, lat, lng in rows
        if (city, country) not in existing
    ]

    if new_rows:
        db.execute(City.__table__.insert(), new_rows)
        db.commit()

    return len(new_rows)


def main() -> None:
    db = SessionLocal()
    try:
        inserted = seed_cities(db)
        total = db.query(City).count()
        print(f"inserted {inserted} new cities ({total} total in table)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
