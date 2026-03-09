"""add pg_trgm extension and location/search indexes

Revision ID: b1c2d3e4f5a6
Revises: a2b3c4d5e6f7
Create Date: 2026-03-09

Adds:
- pg_trgm extension (enables trigram-based GIN indexes for ILIKE '%term%')
- GIN trigram indexes on alumni.first_name and alumni.last_name
  (profile name search goes from full-table-scan to O(log n))
- B-tree index on alumni.location
  (map endpoint GROUP BY and city-detail location filter)
- Composite index on (alumni.show_location, alumni.location)
  (map endpoint WHERE show_location=TRUE AND location IS NOT NULL)
- GIN trigram index on cities.city
  (city autocomplete search uses LIKE 'term%' — B-tree already exists but
   trgm handles mid-string matches too)
"""

from typing import Union

from alembic import op


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable the pg_trgm extension (required for GIN trigram indexes).
    # CREATE EXTENSION IF NOT EXISTS is idempotent.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # GIN trigram indexes on alumni name fields.
    # These allow PostgreSQL to use an index scan for ILIKE '%term%' queries
    # (without trgm, ILIKE with a leading wildcard forces a full table scan).
    op.create_index(
        'ix_alumni_first_name_trgm',
        'alumni',
        ['first_name'],
        postgresql_using='gin',
        postgresql_ops={'first_name': 'gin_trgm_ops'},
    )
    op.create_index(
        'ix_alumni_last_name_trgm',
        'alumni',
        ['last_name'],
        postgresql_using='gin',
        postgresql_ops={'last_name': 'gin_trgm_ops'},
    )

    # B-tree index on alumni.location for exact-match lookups (city detail
    # filter: WHERE location = 'Country, City') and GROUP BY in the map query.
    op.create_index('ix_alumni_location', 'alumni', ['location'])

    # Composite index optimises the map endpoint's leading filter:
    # WHERE show_location = TRUE AND location IS NOT NULL
    op.create_index(
        'ix_alumni_show_location_location',
        'alumni',
        ['show_location', 'location'],
    )

    # GIN trigram index on cities.city to support mid-string city search
    # (the existing B-tree idx_city_name only helps for prefix LIKE 'term%').
    op.create_index(
        'ix_cities_city_trgm',
        'cities',
        ['city'],
        postgresql_using='gin',
        postgresql_ops={'city': 'gin_trgm_ops'},
    )


def downgrade() -> None:
    op.drop_index('ix_cities_city_trgm', table_name='cities')
    op.drop_index('ix_alumni_show_location_location', table_name='alumni')
    op.drop_index('ix_alumni_location', table_name='alumni')
    op.drop_index('ix_alumni_last_name_trgm', table_name='alumni')
    op.drop_index('ix_alumni_first_name_trgm', table_name='alumni')
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
