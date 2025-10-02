"""
Pytest configuration - shared fixtures
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test mode BEFORE importing app
os.environ['TESTING'] = 'true'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-pytest-only'

from main import app
from database import SQLALCHEMY_DATABASE_URL

# Patch JWT secret in auth_utils before any auth happens
import auth_utils
auth_utils.JWT_SECRET = os.environ['JWT_SECRET_KEY']

@pytest.fixture(scope="session")
def test_client():
    """Single test client for all tests"""
    client = TestClient(app)
    return client

@pytest.fixture(scope="session")
def db_engine():
    """Database engine"""
    return create_engine(SQLALCHEMY_DATABASE_URL)

@pytest.fixture
def db_session(db_engine):
    """Fresh database session per test"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="session")
def auth_token(test_client):
    """Authenticate once, reuse token"""
    response = test_client.post("/auth/token", json={
        "email": "admin@owkai.com",
        "password": "admin123"
    })
    
    assert response.status_code == 200, f"Auth failed: {response.text}"
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    """Auth headers for protected endpoints"""
    return {"Authorization": f"Bearer {auth_token}"}
