import os
import uuid
from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")

from app.api.history import router as history_router
from app.db.session import get_db
from app.main import create_app


def make_mock_db():
    async def _mock():
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        result.scalar_one.return_value = 0
        result.scalars.return_value.all.return_value = []
        session.execute.return_value = result
        yield session
    return _mock


def make_test_app():
    app = create_app()
    app.include_router(history_router, prefix="/api/v1/messages/history", tags=["history"])
    return app


@pytest.mark.asyncio
async def test_history_requires_admin():
    app = make_test_app()
    app.dependency_overrides[get_db] = make_mock_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/messages/history")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_history_detail_requires_admin():
    app = make_test_app()
    app.dependency_overrides[get_db] = make_mock_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/messages/history/{uuid.uuid4()}")
    assert response.status_code == 401
