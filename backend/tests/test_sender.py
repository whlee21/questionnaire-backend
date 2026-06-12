import os
from unittest.mock import AsyncMock, MagicMock

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ["FCM_FAKE"] = "1"

from app.schemas.message import SendRequest
from app.services.fcm import FakeFcmClient, reset_fake_client
from app.services.sender import send_notification


@pytest.fixture(autouse=True)
def reset_fcm():
    reset_fake_client()
    yield
    reset_fake_client()


def make_db(prior_event=None, device=None):
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.side_effect = [prior_event] if prior_event else [device]
    session.execute.return_value = result
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_send_broadcast_success():
    fcm = FakeFcmClient()
    db = make_db()

    result = await send_notification(
        db=db,
        fcm=fcm,
        request=SendRequest(
            target={"type": "broadcast"},
            notification={"title": "T", "body": "B"},
        ),
        actor="admin@example.com",
    )

    assert result.success_count == 1
    assert result.failure_count == 0
    assert result.dry_run is False
    assert fcm.sent_messages[0]["topic"] == "all"


@pytest.mark.asyncio
async def test_send_multicast_partial_failure():
    fcm = FakeFcmClient()
    fcm.set_token_response("tok-dead", "UNREGISTERED")
    db = make_db(device=MagicMock())

    result = await send_notification(
        db=db,
        fcm=fcm,
        request=SendRequest(
            target={"type": "tokens", "tokens": ["tok-ok", "tok-dead"]},
            notification={"title": "T", "body": "B"},
        ),
        actor="admin@example.com",
    )

    assert result.success_count == 1
    assert result.failure_count == 1
    assert "tok-dead" in result.invalidated_tokens
    assert db.execute.await_count == 2


@pytest.mark.asyncio
async def test_dry_run_writes_audit():
    fcm = FakeFcmClient()
    db = make_db()

    result = await send_notification(
        db=db,
        fcm=fcm,
        request=SendRequest(
            target={"type": "broadcast"},
            notification={"title": "T", "body": "B"},
            dry_run=True,
        ),
        actor="admin@example.com",
    )

    assert result.dry_run is True
    assert fcm.sent_messages[0]["dry_run"] is True
    db.add.assert_called_once()


@pytest.mark.asyncio
async def test_idempotency_key_returns_prior():
    prior = MagicMock()
    prior.success_count = 5
    prior.failure_count = 0
    prior.dry_run = False
    fcm = FakeFcmClient()
    db = make_db(prior_event=prior)

    result = await send_notification(
        db=db,
        fcm=fcm,
        request=SendRequest(
            target={"type": "broadcast"},
            notification={"title": "T", "body": "B"},
            idempotency_key="my-key",
        ),
        actor="admin@example.com",
    )

    assert result.success_count == 5
    assert len(fcm.sent_messages) == 0
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_oversized_payload_raises():
    fcm = FakeFcmClient()
    db = make_db()

    with pytest.raises(ValueError, match="Payload exceeds"):
        await send_notification(
            db=db,
            fcm=fcm,
            request=SendRequest(
                target={"type": "broadcast"},
                notification={"title": "T", "body": "B"},
                data={"key": "x" * 5000},
            ),
            actor="admin@example.com",
        )


@pytest.mark.asyncio
async def test_transient_error_does_not_invalidate():
    """OTHER errors must NOT invalidate tokens."""
    fcm = FakeFcmClient()
    fcm.set_token_response("tok-transient", "OTHER")
    db = make_db()

    result = await send_notification(
        db=db,
        fcm=fcm,
        request=SendRequest(
            target={"type": "tokens", "tokens": ["tok-transient"]},
            notification={"title": "T", "body": "B"},
        ),
        actor="admin@example.com",
    )

    assert "tok-transient" not in result.invalidated_tokens
    assert result.failure_count == 1
    db.execute.assert_not_awaited()
