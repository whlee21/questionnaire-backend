import uuid
from datetime import datetime, timezone
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.device import PushDevice
from app.schemas.device import RegisterDeviceIn


async def upsert_device(db: AsyncSession, data: RegisterDeviceIn) -> PushDevice:
    now = datetime.now(timezone.utc)
    stmt = (
        insert(PushDevice)
        .values(
            fcm_token=data.fcm_token,
            platform=data.platform,
            app_version=data.app_version,
            installation_id=data.installation_id,
            external_user_id=data.external_user_id,
            last_seen_at=now,
            token_refreshed_at=now,
        )
        .on_conflict_do_update(
            index_elements=["fcm_token"],
            set_={
                "app_version": data.app_version,
                "installation_id": data.installation_id,
                "external_user_id": data.external_user_id,
                "last_seen_at": now,
                "token_refreshed_at": now,
                "updated_at": now,
                "push_enabled": True,
            },
        )
        .returning(PushDevice)
    )
    result = await db.execute(stmt)
    device = result.scalar_one()
    await db.flush()
    return device


async def get_device_by_id(db: AsyncSession, device_id: uuid.UUID) -> PushDevice | None:
    result = await db.execute(select(PushDevice).where(PushDevice.id == device_id))
    return result.scalar_one_or_none()


async def list_devices(
    db: AsyncSession,
    platform: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[PushDevice], int]:
    query = select(PushDevice)
    if platform:
        query = query.where(PushDevice.platform == platform)
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()
    devices_result = await db.execute(
        query.order_by(PushDevice.created_at.desc()).offset((page - 1) * size).limit(size)
    )
    return list(devices_result.scalars().all()), total


async def delete_device(db: AsyncSession, device_id: uuid.UUID) -> bool:
    result = await db.execute(select(PushDevice).where(PushDevice.id == device_id))
    device = result.scalar_one_or_none()
    if device is None:
        return False
    await db.delete(device)
    return True


async def invalidate_device_by_token(db: AsyncSession, fcm_token: str, reason: str) -> None:
    now = datetime.now(timezone.utc)
    await db.execute(
        update(PushDevice)
        .where(PushDevice.fcm_token == fcm_token)
        .values(push_enabled=False, invalidated_at=now, invalid_reason=reason)
    )
