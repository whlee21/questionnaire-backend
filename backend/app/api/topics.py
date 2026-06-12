from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_admin
from app.db.session import get_db
from app.models.admin import AdminUser
from app.models.device import PushDevice
from app.models.topic import PushDeviceTopic, TopicStatus
from app.schemas.topic import TopicOut, TopicSubscribeIn
from app.services.fcm import FcmClient, get_fcm_client

router = APIRouter()
TOPIC_CHUNK_SIZE = 1000


@router.post("/subscribe")
async def subscribe_to_topic(
    body: TopicSubscribeIn,
    db: AsyncSession = Depends(get_db),
    fcm: FcmClient = Depends(get_fcm_client),
    admin: AdminUser = Depends(get_current_admin),
) -> dict:
    tokens = await _resolve_tokens(db, body)
    if not tokens:
        return {"subscribed": 0}
    for i in range(0, len(tokens), TOPIC_CHUNK_SIZE):
        await fcm.subscribe(tokens[i : i + TOPIC_CHUNK_SIZE], body.topic)
    await _upsert_topic_mappings(db, tokens, body.topic, TopicStatus.active)
    return {"subscribed": len(tokens)}


@router.post("/unsubscribe")
async def unsubscribe_from_topic(
    body: TopicSubscribeIn,
    db: AsyncSession = Depends(get_db),
    fcm: FcmClient = Depends(get_fcm_client),
    admin: AdminUser = Depends(get_current_admin),
) -> dict:
    tokens = await _resolve_tokens(db, body)
    if not tokens:
        return {"unsubscribed": 0}
    for i in range(0, len(tokens), TOPIC_CHUNK_SIZE):
        await fcm.unsubscribe(tokens[i : i + TOPIC_CHUNK_SIZE], body.topic)
    await _upsert_topic_mappings(db, tokens, body.topic, TopicStatus.removed)
    return {"unsubscribed": len(tokens)}


@router.get("")
async def list_topics(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> list[TopicOut]:
    result = await db.execute(
        select(PushDeviceTopic.topic, func.count(PushDeviceTopic.id).label("count"))
        .where(PushDeviceTopic.status == TopicStatus.active)
        .group_by(PushDeviceTopic.topic)
        .order_by(PushDeviceTopic.topic)
    )
    return [TopicOut(topic=row.topic, subscriber_count=row.count) for row in result]


async def _resolve_tokens(db: AsyncSession, body: TopicSubscribeIn) -> list[str]:
    if body.tokens:
        return body.tokens
    if body.device_ids:
        result = await db.execute(
            select(PushDevice.fcm_token).where(PushDevice.id.in_(body.device_ids))
        )
        return list(result.scalars().all())
    return []


async def _upsert_topic_mappings(
    db: AsyncSession, tokens: list[str], topic: str, status: TopicStatus
) -> None:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(PushDevice.id, PushDevice.fcm_token).where(PushDevice.fcm_token.in_(tokens))
    )
    device_map = {row.fcm_token: row.id for row in result}
    for token, device_id in device_map.items():
        values: dict = {"device_id": device_id, "topic": topic, "status": status, "subscribed_at": now}
        if status == TopicStatus.removed:
            values["unsubscribed_at"] = now
        stmt = (
            insert(PushDeviceTopic)
            .values(**values)
            .on_conflict_do_update(
                constraint="uq_device_topic",
                set_={"status": status, "unsubscribed_at": now if status == TopicStatus.removed else None},
            )
        )
        await db.execute(stmt)
