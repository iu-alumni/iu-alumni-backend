"""Tests for scripts/seed_cities.py.

Confirms the script actually loads data (not just that it doesn't crash),
that it's safe to re-run, and that the CSV shipped for production
(scripts/data/worldcities.csv) is valid and loads end-to-end.
"""
from app.models.cities import City
from app.models.email_verification import (
    EmailVerification,  # noqa: F401 — registers relationship
)
from app.models.users import Admin, Alumni  # noqa: F401 — registers FK targets
from scripts.seed_cities import CSV_PATH, seed_cities


def _write_csv(tmp_path, rows):
    path = tmp_path / "cities.csv"
    with path.open("w", encoding="utf-8") as f:
        f.write("city,lat,lng,country\n")
        for city, lat, lng, country in rows:
            f.write(f"{city},{lat},{lng},{country}\n")
    return path


def test_seed_cities_inserts_rows(db_session, tmp_path):
    csv_path = _write_csv(
        tmp_path,
        [
            ("Kazan", 55.7964, 49.1089, "Russia"),
            ("Berlin", 52.52, 13.405, "Germany"),
        ],
    )

    inserted = seed_cities(db_session, csv_path=csv_path)

    assert inserted == 3  # 2 from the CSV + Innopolis (always added)
    cities = {(c.city, c.country) for c in db_session.query(City)}
    assert ("Kazan", "Russia") in cities
    assert ("Berlin", "Germany") in cities
    assert ("Innopolis", "Russia") in cities


def test_seed_cities_is_idempotent(db_session, tmp_path):
    csv_path = _write_csv(tmp_path, [("Kazan", 55.7964, 49.1089, "Russia")])

    first_run = seed_cities(db_session, csv_path=csv_path)
    second_run = seed_cities(db_session, csv_path=csv_path)

    assert first_run == 2  # Kazan + Innopolis
    assert second_run == 0
    assert db_session.query(City).count() == 2


def test_seed_cities_dedupes_duplicate_rows_in_csv(db_session, tmp_path):
    csv_path = _write_csv(
        tmp_path,
        [
            ("Kazan", 55.7964, 49.1089, "Russia"),
            ("Kazan", 55.7964, 49.1089, "Russia"),
        ],
    )

    inserted = seed_cities(db_session, csv_path=csv_path)

    assert inserted == 2  # one Kazan row (duplicate dropped) + Innopolis
    assert db_session.query(City).filter(City.city == "Kazan").count() == 1


def test_seed_cities_skips_rows_with_bad_coordinates(db_session, tmp_path):
    path = tmp_path / "cities.csv"
    path.write_text(
        "city,lat,lng,country\nBadRow,not-a-number,49.1089,Russia\n",
        encoding="utf-8",
    )

    inserted = seed_cities(db_session, csv_path=path)

    assert inserted == 1  # only Innopolis; the malformed row is skipped
    assert db_session.query(City).filter(City.city == "BadRow").count() == 0


def test_production_csv_loads_successfully(db_session):
    """Exercises the actual dataset shipped for production, not a fixture."""
    assert CSV_PATH.exists(), f"production seed data missing at {CSV_PATH}"

    inserted = seed_cities(db_session)

    # The real dataset has tens of thousands of cities; a low bar here
    # just confirms the file parsed and loaded rather than silently no-op'ing.
    assert inserted > 1000
    assert db_session.query(City).filter(
        City.city == "Innopolis", City.country == "Russia"
    ).count() == 1
    assert db_session.query(City).filter(City.city == "Tokyo").count() == 1
