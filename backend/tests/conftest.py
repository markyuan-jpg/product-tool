# -*- coding: utf-8 -*-
"""Pytest fixtures for backend tests — uses in-memory SQLite."""

import os, sys
import pytest
import pytest_asyncio
from pathlib import Path

# Ensure backend/ is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ─── Force in-memory SQLite BEFORE any imports ───
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-12345"
os.environ.setdefault("BASE_URL", "http://localhost:3000")

# Must import AFTER setting env vars
from main import app
from database import Base, engine, async_session_factory, User
from auth import create_access_token, hash_password, get_current_user
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture(scope="function")
async def db():
    """Create fresh in-memory database tables for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def session(db):
    """Get an async session for direct DB queries."""
    async with async_session_factory() as sess:
        yield sess


@pytest_asyncio.fixture(scope="function")
async def client(db):
    """Async HTTP test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def auth_headers(session):
    """Create a test user and return auth headers + user object."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("test123456"),
        tier="free",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}, user
