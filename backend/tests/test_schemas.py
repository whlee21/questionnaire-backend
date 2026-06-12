import pytest
from pydantic import ValidationError
from app.schemas.message import (
    SendRequest,
    TokenTarget,
    TokensTarget,
    TopicTarget,
    BroadcastTarget,
)


def test_send_request_token_target():
    req = SendRequest(
        target={"type": "token", "token": "tok-123"},
        notification={"title": "Hello", "body": "World"},
    )
    assert isinstance(req.target, TokenTarget)
    assert req.target.token == "tok-123"
    assert req.dry_run is False


def test_send_request_tokens_target():
    req = SendRequest(
        target={"type": "tokens", "tokens": ["tok-1", "tok-2"]},
        notification={"title": "Hello", "body": "World"},
    )
    assert isinstance(req.target, TokensTarget)
    assert len(req.target.tokens) == 2


def test_send_request_topic_target():
    req = SendRequest(
        target={"type": "topic", "topic": "news"},
        notification={"title": "Hello", "body": "World"},
    )
    assert isinstance(req.target, TopicTarget)
    assert req.target.topic == "news"


def test_send_request_broadcast_target():
    req = SendRequest(
        target={"type": "broadcast"},
        notification={"title": "Hello", "body": "World"},
    )
    assert isinstance(req.target, BroadcastTarget)


def test_send_request_invalid_target_type():
    with pytest.raises(ValidationError):
        SendRequest(
            target={"type": "bogus"},
            notification={"title": "Hello", "body": "World"},
        )


def test_send_request_data_accepts_strings():
    req = SendRequest(
        target={"type": "broadcast"},
        notification={"title": "T", "body": "B"},
        data={"key": "value", "count": "42"},
    )
    assert req.data["key"] == "value"
    assert req.data["count"] == "42"


def test_send_request_idempotency_key():
    req = SendRequest(
        target={"type": "broadcast"},
        notification={"title": "T", "body": "B"},
        idempotency_key="my-key-123",
    )
    assert req.idempotency_key == "my-key-123"


def test_send_request_dry_run_default_false():
    req = SendRequest(
        target={"type": "broadcast"},
        notification={"title": "T", "body": "B"},
    )
    assert req.dry_run is False
