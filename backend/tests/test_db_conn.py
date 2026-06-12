import os
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/test_pushnotify",
)


async def test_db_connectivity():
    engine = create_async_engine(DATABASE_URL, echo=False)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row[0] == 1
    except Exception as exc:
        pytest.skip(f"Database not available (expected in CI without Docker): {exc}")
    finally:
        await engine.dispose()
