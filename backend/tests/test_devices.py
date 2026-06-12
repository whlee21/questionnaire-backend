import os
import uuid
from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")

from app.api.devices import router as devices_router
from app.db.session import get_db
from app.main import create_app
from app.models.device import Platform, PushDevice
from app.services.fcm import FakeFcmClient, get_fcm_client


def make_test_app():
    app = create_app()
    app.include_router(devices_router, prefix="/api/v1/devices", tags=["devices"])
    return app


def make_mock_device(**kwargs) -> MagicMock:
    d = MagicMock(spec=PushDevice)
    d.id = kwargs.get("id", uuid.uuid4())
    d.platform = kwargs.get("platform", Platform.android)
    d.app_version = kwargs.get("app_version", "1.0")
    d.fcm_token = kwargs.get("fcm_token", "tok-test-1234")
    d.push_enabled = kwargs.get("push_enabled", True)
    d.external_user_id = None
    d.last_seen_at = None
    d.created_at = None
    return d


def make_mock_db(device=None):
    async def _mock():
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one.return_value = device or make_mock_device()
        result.scalar_one_or_none.return_value = device
        result.scalars.return_value.all.return_value = []
        result.scalar.return_value = 0
        session.execute.return_value = result
        session.flush = AsyncMock()
        session.delete = AsyncMock()
        yield session
    return _mock


@pytest.mark.asyncio
async def test_register_device_public_no_auth():
    fake_fcm = FakeFcmClient()
    app = make_test_app()
    app.dependency_overrides[get_db] = make_mock_db()
    app.dependency_overrides[get_fcm_client] = lambda: fake_fcm
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/devices/register",
            json={"fcm_token": "tok-1", "platform": "android", "app_version": "1.0"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["registered"] is True


@pytest.mark.asyncio
async def test_register_subscribes_to_all_topic():
    fake_fcm = FakeFcmClient()
    app = make_test_app()
    app.dependency_overrides[get_db] = make_mock_db()
    app.dependency_overrides[get_fcm_client] = lambda: fake_fcm
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/v1/devices/register",
            json={"fcm_token": "tok-1", "platform": "ios", "app_version": "2.0"},
        )
    assert "all" in fake_fcm.subscriptions
    assert "tok-1" in fake_fcm.subscriptions["all"]


@pytest.mark.asyncio
async def test_list_devices_requires_auth():
    app = make_test_app()
    app.dependency_overrides[get_db] = make_mock_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/devices")
    assert response.status_code == 401
