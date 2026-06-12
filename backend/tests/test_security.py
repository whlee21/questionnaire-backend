import os
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")

from app.db.session import get_db
from app.main import create_app


def make_mock_db():
    async def _mock():
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session.execute.return_value = result
        yield session
    return _mock


@pytest.mark.asyncio
async def test_security_headers_present():
    app = create_app()
    app.dependency_overrides[get_db] = make_mock_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"


@pytest.mark.asyncio
async def test_login_rate_limit_triggers_429():
    app = create_app()
    app.dependency_overrides[get_db] = make_mock_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        responses = []
        for _ in range(7):
            r = await client.post(
                "/api/v1/auth/login",
                json={"email": "a@a.com", "password": "wrong"},
            )
            responses.append(r.status_code)
    assert 429 in responses


@pytest.mark.asyncio
async def test_log_scrubbing_masks_long_tokens(caplog):
    import logging
    from app.main import _FcmTokenScrubFilter

    scrubber = _FcmTokenScrubFilter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Sending to token: " + "A" * 150,
        args=(), exc_info=None,
    )
    scrubber.filter(record)
    assert "A" * 150 not in record.msg
    assert "[FCM_TOKEN_REDACTED]" in record.msg
