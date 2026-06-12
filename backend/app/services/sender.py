import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import PushDevice
from app.models.send_event import PushSendEvent
from app.schemas.message import (
    BroadcastTarget,
    SendRequest,
    SendResultOut,
    TokensTarget,
    TokenTarget,
    TopicTarget,
)
from app.services.fcm import BatchResult, FcmClient, TokenResult

logger = logging.getLogger(__name__)

MAX_PAYLOAD_BYTES = 4096
IDEMPOTENCY_WINDOW_HOURS = 24
INVALIDATING_ERROR_CODES = {"UNREGISTERED", "INVALID_ARGUMENT"}


async def send_notification(
    db: AsyncSession,
    fcm: FcmClient,
    request: SendRequest,
    actor: str,
) -> SendResultOut:
    """Orchestrate a push send: resolve target, call FCM, cleanup, audit."""
    if request.idempotency_key:
        prior = await _find_prior_send(db, request.idempotency_key)
        if prior:
            return SendResultOut(
                success_count=prior.success_count,
                failure_count=prior.failure_count,
                invalidated_tokens=[],
                dry_run=prior.dry_run,
            )

    _validate_payload_size(request)

    data = {key: str(value) for key, value in request.data.items()}
    notification = request.notification.model_dump(exclude_none=True)

    target = request.target
    batch_result: BatchResult | None = None
    topic_result: TokenResult | None = None

    if isinstance(target, TokenTarget):
        target_type = "token"
        target_summary = _mask_token(target.token)
        single_result = await fcm.send_one(
            target.token,
            notification,
            data,
            request.dry_run,
        )
        batch_result = BatchResult(token_results=[single_result])
    elif isinstance(target, TokensTarget):
        target_type = "tokens"
        target_summary = f"{len(target.tokens)} tokens"
        batch_result = await fcm.send_many(
            target.tokens,
            notification,
            data,
            request.dry_run,
        )
    elif isinstance(target, TopicTarget):
        target_type = "topic"
        target_summary = target.topic
        topic_result = await fcm.send_topic(
            target.topic,
            notification,
            data,
            request.dry_run,
        )
    elif isinstance(target, BroadcastTarget):
        target_type = "broadcast"
        target_summary = "all"
        topic_result = await fcm.send_topic(
            "all",
            notification,
            data,
            request.dry_run,
        )
    else:
        raise ValueError(f"Unknown target type: {type(target)}")

    if batch_result is not None:
        success_count = batch_result.success_count
        failure_count = batch_result.failure_count
        invalidated_tokens = batch_result.invalidated_tokens
    else:
        success_count = 1 if topic_result and topic_result.success else 0
        failure_count = 0 if success_count else 1
        invalidated_tokens = []

    if not request.dry_run and batch_result is not None:
        await _invalidate_failed_tokens(db, batch_result)

    event = PushSendEvent(
        actor=actor,
        target_type=target_type,
        target_summary=target_summary,
        payload_summary={
            "title": request.notification.title,
            "body": request.notification.body,
        },
        dry_run=request.dry_run,
        success_count=success_count,
        failure_count=failure_count,
        idempotency_key=request.idempotency_key,
    )
    db.add(event)
    await db.flush()

    return SendResultOut(
        success_count=success_count,
        failure_count=failure_count,
        invalidated_tokens=invalidated_tokens,
        dry_run=request.dry_run,
    )


def _validate_payload_size(request: SendRequest) -> None:
    payload_json = json.dumps({
        "notification": request.notification.model_dump(),
        "data": request.data,
    })
    if len(payload_json.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ValueError(f"Payload exceeds {MAX_PAYLOAD_BYTES} bytes")


async def _invalidate_failed_tokens(db: AsyncSession, batch_result: BatchResult) -> None:
    now = datetime.now(timezone.utc)
    for token_result in batch_result.token_results:
        if token_result.error_code not in INVALIDATING_ERROR_CODES:
            continue

        result = await db.execute(
            select(PushDevice).where(PushDevice.fcm_token == token_result.token)
        )
        if result.scalar_one_or_none() is None:
            continue

        await db.execute(
            update(PushDevice)
            .where(PushDevice.fcm_token == token_result.token)
            .values(
                push_enabled=False,
                invalidated_at=now,
                invalid_reason=token_result.error_code,
            )
        )


def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "****"
    return f"{token[:4]}...{token[-4:]}"


async def _find_prior_send(db: AsyncSession, idempotency_key: str) -> PushSendEvent | None:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=IDEMPOTENCY_WINDOW_HOURS)
    result = await db.execute(
        select(PushSendEvent)
        .where(
            PushSendEvent.idempotency_key == idempotency_key,
            PushSendEvent.created_at >= cutoff,
        )
        .order_by(PushSendEvent.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
