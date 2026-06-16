import logging

import httpx
import pytest

from app.main import create_app


@pytest.mark.asyncio
async def test_health_returns_ok():
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_no_auth_required():
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200


def test_startup_logs_config_at_debug(caplog):
    with caplog.at_level(logging.DEBUG, logger="app.main"):
        create_app()

    debug_msgs = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
    config_msgs = [m for m in debug_msgs if m.startswith("config ")]

    assert any("FCM_FAKE" in m for m in config_msgs)
    assert any("LOG_LEVEL" in m for m in config_msgs)
    assert any("CORS_ORIGINS" in m for m in config_msgs)


def test_startup_masks_sensitive_fields(caplog):
    with caplog.at_level(logging.DEBUG, logger="app.main"):
        create_app()

    config_msgs = [r.message for r in caplog.records if r.message.startswith("config ")]

    jwt_msgs = [m for m in config_msgs if "JWT_SECRET" in m]
    assert jwt_msgs, "JWT_SECRET should be logged"
    assert not any("changeme" in m for m in jwt_msgs), "JWT_SECRET value must be masked"

    pw_msgs = [m for m in config_msgs if "ADMIN_PASSWORD" in m]
    assert pw_msgs, "ADMIN_PASSWORD should be logged"
    for m in pw_msgs:
        parts = m.split(" = ", 1)
        if len(parts) == 2 and parts[1] not in ("", "****"):
            assert parts[1].endswith("****"), f"ADMIN_PASSWORD not masked: {m}"
