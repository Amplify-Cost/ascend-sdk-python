# tests/conftest.py
import pytest_asyncio
from httpx import AsyncClient
from httpx import ASGITransport
from main import app

@pytest_asyncio.fixture(scope="module")
async def test_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
