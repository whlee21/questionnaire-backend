import os
import pytest

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/test_pushnotify",
)
