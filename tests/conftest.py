import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.users import Admin, Alumni
from app.core.security import get_password_hash, get_random_token

# Test database URL - use a separate PostgreSQL database for testing
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/test_iu_alumni"
)

# Create test database engine
engine = create_engine(TEST_DATABASE_URL)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session for each test
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        
    # Drop all tables after the test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    # Override the get_db dependency to use the test database
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Reset the dependency override
    app.dependency_overrides = {}

@pytest.fixture(scope="function")
def test_admin(db):
    admin = Admin(
        id=get_random_token(),
        email="admin@test.com",
        hashed_password=get_password_hash("adminpassword")
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

@pytest.fixture(scope="function")
def test_alumni(db):
    alumni = Alumni(
        id=get_random_token(),
        email="alumni@test.com",
        hashed_password=get_password_hash("alumnipassword"),
        first_name="Test",
        last_name="User",
        graduation_year="2023",
        location="Test City",
        biography="Test biography",
        show_location=True,
        is_verified=True,
        is_banned=False
    )
    db.add(alumni)
    db.commit()
    db.refresh(alumni)
    return alumni
