import os

import httpx
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")

from app.main import create_app


@pytest.mark.asyncio
async def test_app_creates_successfully():
    """Verify the full app factory creates without errors."""
    app = create_app()
    assert app is not None
    assert app.title == "PushNotify API"


@pytest.mark.asyncio
async def test_health_endpoint_works():
    """Health endpoint returns 200 with status ok."""
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_all_api_routes_registered():
    """Verify all expected API routes are registered."""
    app = create_app()
    routes = {route.path for route in app.routes}
    expected = [
        "/api/v1/auth/login",
        "/api/v1/auth/me",
        "/api/v1/devices/register",
        "/api/v1/devices",
        "/api/v1/messages/send",
        "/api/v1/topics/subscribe",
        "/api/v1/topics/unsubscribe",
        "/api/v1/topics",
        "/api/v1/messages/history",
    ]
    for path in expected:
        assert path in routes, f"Route {path} not registered"


@pytest.mark.asyncio
async def test_security_headers_on_health():
    """Security headers must be present."""
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
