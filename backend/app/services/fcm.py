from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from fastapi.concurrency import run_in_threadpool

from app.core.config import get_settings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
TOPIC_CHUNK_SIZE = 1000


@dataclass
class TokenResult:
    token: str
    success: bool
    error_code: str | None = None
    message_id: str | None = None


@dataclass
class BatchResult:
    token_results: list[TokenResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.token_results if r.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self.token_results if not r.success)

    @property
    def invalidated_tokens(self) -> list[str]:
        return [
            r.token
            for r in self.token_results
            if r.error_code in ("UNREGISTERED", "INVALID_ARGUMENT")
        ]

    @property
    def message_ids(self) -> list[str]:
        return [r.message_id for r in self.token_results if r.success and r.message_id]


@runtime_checkable
class FcmClient(Protocol):
    async def send_one(
        self,
        token: str,
        notification: dict,
        data: dict[str, str],
        dry_run: bool = False,
    ) -> TokenResult: ...

    async def send_many(
        self,
        tokens: list[str],
        notification: dict,
        data: dict[str, str],
        dry_run: bool = False,
    ) -> BatchResult: ...

    async def send_topic(
        self,
        topic: str,
        notification: dict,
        data: dict[str, str],
        dry_run: bool = False,
    ) -> TokenResult: ...

    async def subscribe(self, tokens: list[str], topic: str) -> None: ...

    async def unsubscribe(self, tokens: list[str], topic: str) -> None: ...


class FirebaseFcmClient:
    """Real FCM client using firebase-admin SDK (HTTP v1 only, NOT legacy server-key)."""

    _initialized: bool = False

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        import firebase_admin
        from firebase_admin import credentials

        settings = get_settings()
        if not firebase_admin._apps:
            if settings.GOOGLE_APPLICATION_CREDENTIALS:
                cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
            else:
                cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(
                cred, {"projectId": settings.FIREBASE_PROJECT_ID}
            )
        self._initialized = True

    @staticmethod
    def _coerce_data(data: dict) -> dict[str, str]:
        """FCM requires ALL data values to be strings."""
        return {k: str(v) for k, v in data.items()}

    @staticmethod
    def _map_error(exc: Exception) -> str:
        exc_str = str(exc)
        if "UNREGISTERED" in exc_str or "registration-token-not-registered" in exc_str:
            return "UNREGISTERED"
        if "INVALID_ARGUMENT" in exc_str or "invalid-argument" in exc_str:
            return "INVALID_ARGUMENT"
        return "OTHER"

    async def send_one(
        self,
        token: str,
        notification: dict,
        data: dict[str, str],
        dry_run: bool = False,
    ) -> TokenResult:
        from firebase_admin import messaging

        def _send() -> str:
            self._ensure_initialized()
            msg = messaging.Message(
                token=token,
                notification=messaging.Notification(
                    title=notification.get("title"),
                    body=notification.get("body"),
                    image=notification.get("image_url"),
                ),
                data=self._coerce_data(data),
            )
            return messaging.send(msg, dry_run=dry_run)

        try:
            message_id: str = await run_in_threadpool(_send)
            return TokenResult(token=token, success=True, message_id=message_id)
        except Exception as exc:
            error_code = self._map_error(exc)
            logger.warning("FCM send_one failed token=%s... code=%s", token[:8], error_code)
            return TokenResult(token=token, success=False, error_code=error_code)

    async def send_many(
        self,
        tokens: list[str],
        notification: dict,
        data: dict[str, str],
        dry_run: bool = False,
    ) -> BatchResult:
        from firebase_admin import messaging

        all_results: list[TokenResult] = []

        for i in range(0, len(tokens), CHUNK_SIZE):
            chunk = tokens[i : i + CHUNK_SIZE]

            def _send_chunk(chunk: list[str] = chunk):
                self._ensure_initialized()
                msg = messaging.MulticastMessage(
                    tokens=chunk,
                    notification=messaging.Notification(
                        title=notification.get("title"),
                        body=notification.get("body"),
                        image=notification.get("image_url"),
                    ),
                    data=self._coerce_data(data),
                )
                return messaging.send_each_for_multicast(msg, dry_run=dry_run)

            try:
                batch_response = await run_in_threadpool(_send_chunk)
                for j, resp in enumerate(batch_response.responses):
                    tok = chunk[j]
                    if resp.success:
                        all_results.append(
                            TokenResult(token=tok, success=True, message_id=resp.message_id)
                        )
                    else:
                        error_code = (
                            self._map_error(resp.exception) if resp.exception else "OTHER"
                        )
                        all_results.append(
                            TokenResult(token=tok, success=False, error_code=error_code)
                        )
            except Exception as exc:
                error_code = self._map_error(exc)
                for tok in chunk:
                    all_results.append(
                        TokenResult(token=tok, success=False, error_code=error_code)
                    )

        return BatchResult(token_results=all_results)

    async def send_topic(
        self,
        topic: str,
        notification: dict,
        data: dict[str, str],
        dry_run: bool = False,
    ) -> TokenResult:
        from firebase_admin import messaging

        def _send() -> str:
            self._ensure_initialized()
            msg = messaging.Message(
                topic=topic,
                notification=messaging.Notification(
                    title=notification.get("title"),
                    body=notification.get("body"),
                    image=notification.get("image_url"),
                ),
                data=self._coerce_data(data),
            )
            return messaging.send(msg, dry_run=dry_run)

        try:
            message_id: str = await run_in_threadpool(_send)
            return TokenResult(token=f"topic:{topic}", success=True, message_id=message_id)
        except Exception as exc:
            error_code = self._map_error(exc)
            return TokenResult(token=f"topic:{topic}", success=False, error_code=error_code)

    async def subscribe(self, tokens: list[str], topic: str) -> None:
        from firebase_admin import messaging

        for i in range(0, len(tokens), TOPIC_CHUNK_SIZE):
            chunk = tokens[i : i + TOPIC_CHUNK_SIZE]

            def _sub(chunk: list[str] = chunk) -> None:
                self._ensure_initialized()
                messaging.subscribe_to_topic(chunk, topic)

            await run_in_threadpool(_sub)

    async def unsubscribe(self, tokens: list[str], topic: str) -> None:
        from firebase_admin import messaging

        for i in range(0, len(tokens), TOPIC_CHUNK_SIZE):
            chunk = tokens[i : i + TOPIC_CHUNK_SIZE]

            def _unsub(chunk: list[str] = chunk) -> None:
                self._ensure_initialized()
                messaging.unsubscribe_from_topic(chunk, topic)

            await run_in_threadpool(_unsub)


class FakeFcmClient:
    """In-memory FCM client. No Firebase credentials needed. Used for all QA."""

    def __init__(self) -> None:
        self.sent_messages: list[dict] = []
        self._token_responses: dict[str, str | None] = {}
        self.subscriptions: dict[str, set[str]] = {}
        self._msg_counter: int = 0

    def _next_message_id(self) -> str:
        self._msg_counter += 1
        return f"projects/fake-project/messages/fake-{self._msg_counter:06d}"

    def set_token_response(self, token: str, error_code: str | None) -> None:
        """Configure a token to return a specific error code (None = success)."""
        self._token_responses[token] = error_code

    async def send_one(
        self,
        token: str,
        notification: dict,
        data: dict[str, str],
        dry_run: bool = False,
    ) -> TokenResult:
        message_id = self._next_message_id()
        self.sent_messages.append({
            "type": "single",
            "token": token,
            "notification": notification,
            "data": {k: str(v) for k, v in data.items()},
            "dry_run": dry_run,
            "message_id": message_id,
        })
        error_code = self._token_responses.get(token)
        return TokenResult(
            token=token,
            success=error_code is None,
            error_code=error_code,
            message_id=message_id if error_code is None else None,
        )

    async def send_many(
        self,
        tokens: list[str],
        notification: dict,
        data: dict[str, str],
        dry_run: bool = False,
    ) -> BatchResult:
        coerced_data = {k: str(v) for k, v in data.items()}
        all_results: list[TokenResult] = []

        for i in range(0, len(tokens), CHUNK_SIZE):
            chunk = tokens[i : i + CHUNK_SIZE]
            self.sent_messages.append({
                "type": "multicast_chunk",
                "tokens": chunk,
                "notification": notification,
                "data": coerced_data,
                "dry_run": dry_run,
            })
            for token in chunk:
                error_code = self._token_responses.get(token)
                message_id = self._next_message_id() if error_code is None else None
                all_results.append(
                    TokenResult(
                        token=token,
                        success=error_code is None,
                        error_code=error_code,
                        message_id=message_id,
                    )
                )

        return BatchResult(token_results=all_results)

    async def send_topic(
        self,
        topic: str,
        notification: dict,
        data: dict[str, str],
        dry_run: bool = False,
    ) -> TokenResult:
        message_id = self._next_message_id()
        self.sent_messages.append({
            "type": "topic",
            "topic": topic,
            "notification": notification,
            "data": {k: str(v) for k, v in data.items()},
            "dry_run": dry_run,
            "message_id": message_id,
        })
        return TokenResult(token=f"topic:{topic}", success=True, message_id=message_id)

    async def subscribe(self, tokens: list[str], topic: str) -> None:
        self.subscriptions.setdefault(topic, set()).update(tokens)

    async def unsubscribe(self, tokens: list[str], topic: str) -> None:
        if topic in self.subscriptions:
            self.subscriptions[topic].difference_update(tokens)


_fake_client: FakeFcmClient | None = None


def get_fcm_client() -> FcmClient:
    """FastAPI dependency: FakeFcmClient if FCM_FAKE=1, else FirebaseFcmClient."""
    global _fake_client
    fake_env = os.getenv("FCM_FAKE", "").lower() in {"1", "true", "yes", "on"}
    if fake_env or get_settings().FCM_FAKE:
        if _fake_client is None:
            _fake_client = FakeFcmClient()
        return _fake_client
    return FirebaseFcmClient()


def reset_fake_client() -> None:
    """Reset the fake client singleton (call in test teardown for isolation)."""
    global _fake_client
    _fake_client = None
