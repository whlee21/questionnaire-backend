import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_admin
from app.db.session import get_db
from app.models.admin import AdminUser
from app.repositories.device import delete_device, list_devices, upsert_device
from app.schemas.common import PaginatedResponse
from app.schemas.device import DeviceOut, DeviceRegisteredOut, RegisterDeviceIn
from app.services.fcm import FcmClient, get_fcm_client

router = APIRouter()
_limiter = Limiter(key_func=get_remote_address)


def mask_token(token: str) -> str:
    if len(token) <= 8:
        return "***"
    return token[:4] + "..." + token[-4:]


@router.post("/register", response_model=DeviceRegisteredOut, status_code=200)
@_limiter.limit("10/minute")
async def register_device(
    request: Request,
    body: RegisterDeviceIn,
    db: AsyncSession = Depends(get_db),
    fcm: FcmClient = Depends(get_fcm_client),
) -> DeviceRegisteredOut:
    device = await upsert_device(db, body)
    await fcm.subscribe([body.fcm_token], "all")
    return DeviceRegisteredOut(id=device.id)


@router.get("", response_model=PaginatedResponse[DeviceOut])
async def list_devices_admin(
    platform: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> PaginatedResponse[DeviceOut]:
    devices, total = await list_devices(db, platform=platform, page=page, size=size)
    items = [
        DeviceOut(
            id=d.id, platform=d.platform, app_version=d.app_version,
            fcm_token_masked=mask_token(d.fcm_token), push_enabled=d.push_enabled,
            external_user_id=d.external_user_id, last_seen_at=d.last_seen_at,
            created_at=d.created_at,
        )
        for d in devices
    ]
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.delete("/{device_id}", status_code=204)
async def delete_device_admin(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> None:
    deleted = await delete_device(db, device_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
