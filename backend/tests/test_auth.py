import os
import uuid
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test"
)

from app.core.security import create_access_token, hash_password
from app.db.session import get_db
from app.main import create_app
from app.models.admin import AdminUser


def make_test_admin(email: str = "admin@example.com", password: str = "password123") -> MagicMock:
    admin = MagicMock(spec=AdminUser)
    admin.id = uuid.uuid4()
    admin.email = email
    admin.hashed_password = hash_password(password)
    admin.is_active = True
    return admin


def make_mock_db(admin: AdminUser | None):
    async def _mock_get_db():
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = admin
        session.execute.return_value = result
        yield session

    return _mock_get_db


@pytest.mark.asyncio
async def test_login_success():
    admin = make_test_admin()
    app = create_app()
    app.dependency_overrides[get_db] = make_mock_db(admin)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "password123"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password():
    admin = make_test_admin()
    app = create_app()
    app.dependency_overrides[get_db] = make_mock_db(admin)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "wrong_password"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_user_not_found():
    app = create_app()
    app.dependency_overrides[get_db] = make_mock_db(None)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "password"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_without_token():
    app = create_app()
    app.dependency_overrides[get_db] = make_mock_db(None)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_valid_token():
    admin = make_test_admin()
    app = create_app()
    app.dependency_overrides[get_db] = make_mock_db(admin)

    token = create_access_token({"sub": admin.email})

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == admin.email


@pytest.mark.asyncio
async def test_protected_route_with_invalid_token():
    app = create_app()
    app.dependency_overrides[get_db] = make_mock_db(None)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

    assert response.status_code == 401
