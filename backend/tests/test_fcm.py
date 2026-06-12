import os

import pytest

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test"
)
os.environ["FCM_FAKE"] = "1"

from app.services.fcm import (  # noqa: E402
    FakeFcmClient,
    get_fcm_client,
    reset_fake_client,
)


@pytest.fixture(autouse=True)
def isolate_fake_client():
    reset_fake_client()
    yield
    reset_fake_client()


def test_get_fcm_client_returns_fake_when_fcm_fake_set():
    client = get_fcm_client()
    assert isinstance(client, FakeFcmClient)
    assert type(client).__name__ == "FakeFcmClient"


@pytest.mark.asyncio
async def test_send_many_chunks_over_500():
    """1200 tokens → 3 batches (500 + 500 + 200)."""
    client = FakeFcmClient()
    tokens = [f"tok-{i}" for i in range(1200)]
    result = await client.send_many(tokens, {"title": "T", "body": "B"}, {})

    chunks = [m for m in client.sent_messages if m["type"] == "multicast_chunk"]
    assert len(chunks) == 3
    assert len(chunks[0]["tokens"]) == 500
    assert len(chunks[1]["tokens"]) == 500
    assert len(chunks[2]["tokens"]) == 200
    assert result.success_count == 1200
    assert result.failure_count == 0


@pytest.mark.asyncio
async def test_unregistered_token_surfaces_error_code():
    """Token scripted UNREGISTERED → appears in invalidated_tokens."""
    client = FakeFcmClient()
    client.set_token_response("tok-dead", "UNREGISTERED")

    result = await client.send_many(
        ["tok-ok", "tok-dead"],
        {"title": "T", "body": "B"},
        {},
    )

    assert result.success_count == 1
    assert result.failure_count == 1
    assert "tok-dead" in result.invalidated_tokens
    assert "tok-ok" not in result.invalidated_tokens

    dead = next(r for r in result.token_results if r.token == "tok-dead")
    assert dead.error_code == "UNREGISTERED"
    assert not dead.success


@pytest.mark.asyncio
async def test_data_values_coerced_to_strings():
    """All data values must be strings (FCM requirement)."""
    client = FakeFcmClient()
    await client.send_many(
        ["tok-1"],
        {"title": "T", "body": "B"},
        {"count": 42, "flag": True, "name": "test"},  # type: ignore[arg-type]
    )
    msg = client.sent_messages[0]
    assert all(isinstance(v, str) for v in msg["data"].values())
    assert msg["data"]["count"] == "42"
    assert msg["data"]["flag"] == "True"


@pytest.mark.asyncio
async def test_send_topic():
    client = FakeFcmClient()
    result = await client.send_topic("news", {"title": "T", "body": "B"}, {})
    assert result.success
    assert result.token == "topic:news"
    assert client.sent_messages[0]["type"] == "topic"


@pytest.mark.asyncio
async def test_subscribe_and_unsubscribe():
    client = FakeFcmClient()
    await client.subscribe(["tok-1", "tok-2"], "news")
    assert "tok-1" in client.subscriptions["news"]
    await client.unsubscribe(["tok-1"], "news")
    assert "tok-1" not in client.subscriptions["news"]
    assert "tok-2" in client.subscriptions["news"]


@pytest.mark.asyncio
async def test_dry_run_flag_passed_through():
    client = FakeFcmClient()
    await client.send_many(["tok-1"], {"title": "T", "body": "B"}, {}, dry_run=True)
    assert client.sent_messages[0]["dry_run"] is True


@pytest.mark.asyncio
async def test_invalid_argument_in_invalidated_tokens():
    """INVALID_ARGUMENT tokens should also be in invalidated_tokens."""
    client = FakeFcmClient()
    client.set_token_response("tok-invalid", "INVALID_ARGUMENT")
    result = await client.send_many(["tok-invalid"], {"title": "T", "body": "B"}, {})
    assert "tok-invalid" in result.invalidated_tokens


@pytest.mark.asyncio
async def test_other_error_not_in_invalidated_tokens():
    """OTHER errors (transient) should NOT be in invalidated_tokens."""
    client = FakeFcmClient()
    client.set_token_response("tok-transient", "OTHER")
    result = await client.send_many(["tok-transient"], {"title": "T", "body": "B"}, {})
    assert "tok-transient" not in result.invalidated_tokens
    assert result.failure_count == 1
