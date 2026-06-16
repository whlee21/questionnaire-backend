import logging
import os
import uuid
from unittest.mock import MagicMock

import httpx
import pytest

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test"
)

from app.api.auth import get_current_admin
from app.main import create_app
from app.models.admin import AdminUser


def make_test_admin(email: str = "admin@example.com") -> MagicMock:
    admin = MagicMock(spec=AdminUser)
    admin.id = uuid.uuid4()
    admin.email = email
    admin.is_active = True
    return admin


@pytest.mark.asyncio
async def test_get_log_level_requires_auth():
    app = create_app()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/admin/log-level")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_put_log_level_requires_auth():
    app = create_app()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/api/v1/admin/log-level", json={"level": "DEBUG"}
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_log_level_returns_current():
    admin = make_test_admin()
    app = create_app()
    app.dependency_overrides[get_current_admin] = lambda: admin
    logging.root.setLevel(logging.INFO)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/admin/log-level")

    assert response.status_code == 200
    assert response.json()["level"] == "INFO"


@pytest.mark.asyncio
async def test_put_log_level_changes_level():
    admin = make_test_admin()
    app = create_app()
    app.dependency_overrides[get_current_admin] = lambda: admin

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/api/v1/admin/log-level", json={"level": "DEBUG"}
        )

    assert response.status_code == 200
    assert response.json()["level"] == "DEBUG"
    assert logging.root.level == logging.DEBUG
    logging.root.setLevel(logging.INFO)


@pytest.mark.asyncio
async def test_put_log_level_all_valid_levels():
    admin = make_test_admin()
    app = create_app()
    app.dependency_overrides[get_current_admin] = lambda: admin

    for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                "/api/v1/admin/log-level", json={"level": level}
            )
        assert response.status_code == 200
        assert response.json()["level"] == level
    logging.root.setLevel(logging.INFO)


@pytest.mark.asyncio
async def test_put_log_level_invalid_level_returns_422():
    admin = make_test_admin()
    app = create_app()
    app.dependency_overrides[get_current_admin] = lambda: admin

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/api/v1/admin/log-level", json={"level": "VERBOSE"}
        )

    assert response.status_code == 422


def test_log_level_from_env_is_honored(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    create_app()
    assert logging.root.level == logging.WARNING
    logging.root.setLevel(logging.INFO)


def test_invalid_log_level_in_env_fails_fast(monkeypatch):
    from pydantic import ValidationError

    monkeypatch.setenv("LOG_LEVEL", "BOGUS")
    with pytest.raises(ValidationError):
        create_app()
