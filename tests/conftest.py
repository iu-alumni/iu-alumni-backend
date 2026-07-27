"""Pytest configuration and shared fixtures for the test suite."""

import os


# ---------------------------------------------------------------------------
# 1. Set required environment variables FIRST (before any app imports)
# ---------------------------------------------------------------------------
_TEST_ENV = {
    "SQLALCHEMY_DATABASE_URL": "sqlite:///:memory:",
    "SECRET_KEY": "test-secret-key-for-testing-purposes-only-32c",
    "EMAIL_HASH_SECRET": "test-email-hash-secret-for-tests-only!!!",
    "ADMIN_EMAIL": "admin@innopolis.university",
    "ADMIN_PASSWORD": "adminpassword123",
    "ENVIRONMENT": "TEST",
}
for _key, _val in _TEST_ENV.items():
    os.environ[_key] = _val

# ---------------------------------------------------------------------------
# 2. Prevent load_dotenv from overriding the test variables above
# ---------------------------------------------------------------------------
import dotenv


dotenv.load_dotenv = lambda **_kwargs: None

# ---------------------------------------------------------------------------
# 3. NOW import app modules (after environment is set)
# ---------------------------------------------------------------------------
import pytest
from sqlalchemy import JSON, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base


# ---------------------------------------------------------------------------
# 4. Test database fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def engine():
    """Create a shared in-memory SQLite engine for tests."""
    return create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
def tables(engine):
    """Create all database tables with JSON instead of ARRAY for SQLite."""
    from app.models.badge import Badge, UserBadge
    from app.models.events import Event
    from app.models.projects import Project
    from app.models.settings import Setting
    from app.models.telegram import Poll

    # Replace ARRAY with JSON for SQLite compatibility
    for column in Event.__table__.columns:
        if column.type.__class__.__name__ == "ARRAY":
            column.type = JSON()

    for column in Project.__table__.columns:
        if column.type.__class__.__name__ == "ARRAY":
            column.type = JSON()

    for column in Poll.__table__.columns:
        if column.type.__class__.__name__ == "ARRAY":
            column.type = JSON()

    # Exclude tables that use PostgreSQL-specific types (JSONB, ARRAY)
    excluded_tables = {
        Setting.__table__,    # has JSONB
        Badge.__table__,      # has JSONB and ARRAY
        UserBadge.__table__,  # has JSONB
    }
    all_tables = set(Base.metadata.tables.values())
    tables_to_create = all_tables - excluded_tables

    for table in tables_to_create:
        table.create(bind=engine, checkfirst=True)

    yield

    for table in reversed(list(tables_to_create)):
        table.drop(bind=engine, checkfirst=True)


@pytest.fixture
def db_session(engine, tables):
    """Create a test database session using a nested transaction."""
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    """Create a test client for FastAPI with overridden dependencies."""
    from fastapi import FastAPI
    from fastapi.routing import APIRouter
    from fastapi.testclient import TestClient

    from app.api.routes.admin import router as admin_router
    from app.api.routes.authentication import router as auth_router
    from app.api.routes.cities import router as cities_router
    from app.api.routes.events import router as events_router
    from app.api.routes.notifications import router as notifications_router
    from app.api.routes.profile import router as profile_router
    from app.api.routes.projects import router as projects_router
    from app.api.routes.telegram import router as telegram_router
    from app.core.database import get_db

    app = FastAPI()
    api_v1 = APIRouter(prefix="/api/v1")
    api_v1.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    api_v1.include_router(profile_router, prefix="/profile", tags=["Profile"])
    api_v1.include_router(events_router, prefix="/events", tags=["Events"])
    api_v1.include_router(admin_router, prefix="/admin", tags=["Admin"])
    api_v1.include_router(cities_router, prefix="/cities", tags=["Cities"])
    api_v1.include_router(projects_router, prefix="/projects", tags=["Projects"])
    api_v1.include_router(
        notifications_router, prefix="/notifications", tags=["Notifications"]
    )
    app.include_router(api_v1)
    app.include_router(telegram_router, tags=["Telegram"])

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client
