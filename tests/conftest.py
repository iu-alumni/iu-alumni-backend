
"""Pytest configuration and shared fixtures for the test suite.

Environment variables must be set *before* any app module is imported because
``app/core/database.py`` calls ``create_engine`` and ``load_dotenv`` at import
time.  Patching ``dotenv.load_dotenv`` here ensures a local ``.env`` file cannot
override the in-memory SQLite URL used during testing.
"""

import os  # noqa: I001

# ---------------------------------------------------------------------------
# 1. Set required environment variables before any app imports
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
# 2. Prevent load_dotenv from overriding the test variables above.
#    database.py does ``from dotenv import load_dotenv`` at import time, so
#    replacing the function on the module object before that import is enough.
# ---------------------------------------------------------------------------
import dotenv  # noqa: E402, I001

dotenv.load_dotenv = lambda **_kwargs: None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# 3. Import app modules after environment setup
# ---------------------------------------------------------------------------
import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base  # noqa: E402


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
    """Create all database tables except those with ARRAY (not supported by SQLite)."""
    from app.models.events import Event
    from app.models.telegram import Poll

    excluded_tables = {Event.__table__, Poll.__table__}
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
    from app.api.routes.profile import router as profile_router
    from app.api.routes.telegram import router as telegram_router
    from app.core.database import get_db

    # Create a test app without lifespan
    app = FastAPI()
    api_v1 = APIRouter(prefix="/api/v1")
    api_v1.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    api_v1.include_router(profile_router, prefix="/profile", tags=["Profile"])
    api_v1.include_router(events_router, prefix="/events", tags=["Events"])
    api_v1.include_router(admin_router, prefix="/admin", tags=["Admin"])
    api_v1.include_router(cities_router, prefix="/cities", tags=["Cities"])
    app.include_router(api_v1)
    app.include_router(telegram_router, tags=["Telegram"])

    # Override the get_db dependency to use the test session
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client
