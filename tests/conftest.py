"""
Pytest configuration and fixtures
Shared across all test files
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Import app AFTER setting environment
os.environ['TESTING'] = 'true'
from main import app
from database import SQLALCHEMY_DATABASE_URL

@pytest.fixture(scope="session")
def test_client():
    """Shared test client for all tests"""
    return TestClient(app)

@pytest.fixture(scope="session")
def db_engine():
    """Database engine for tests"""
    return create_engine(SQLALCHEMY_DATABASE_URL)

@pytest.fixture
def db_session(db_engine):
    """Database session for each test"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="session")
def auth_token(test_client):
    """Get authentication token once for all tests"""
    response = test_client.post("/auth/token", json={
        "email": "admin@owkai.com",
        "password": "admin123"
    })
    
    if response.status_code != 200:
        pytest.fail(f"Authentication failed: {response.text}")
    
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    """Authentication headers for protected endpoints"""
    return {"Authorization": f"Bearer {auth_token}"}
