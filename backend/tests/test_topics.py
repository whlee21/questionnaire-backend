import os
from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")

from app.api.topics import router as topics_router
from app.db.session import get_db
from app.main import create_app


def make_mock_db():
    async def _mock():
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        result.scalars.return_value.all.return_value = []
        result.__iter__ = MagicMock(return_value=iter([]))
        session.execute.return_value = result
        yield session
    return _mock


@pytest.mark.asyncio
async def test_subscribe_requires_admin():
    app = create_app()
    app.include_router(topics_router, prefix="/api/v1/topics", tags=["topics"])
    app.dependency_overrides[get_db] = make_mock_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/topics/subscribe",
            json={"topic": "news", "tokens": ["tok-1"]},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unsubscribe_requires_admin():
    app = create_app()
    app.include_router(topics_router, prefix="/api/v1/topics", tags=["topics"])
    app.dependency_overrides[get_db] = make_mock_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/topics/unsubscribe",
            json={"topic": "news", "tokens": ["tok-1"]},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_topics_requires_admin():
    app = create_app()
    app.include_router(topics_router, prefix="/api/v1/topics", tags=["topics"])
    app.dependency_overrides[get_db] = make_mock_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/topics")
    assert response.status_code == 401
