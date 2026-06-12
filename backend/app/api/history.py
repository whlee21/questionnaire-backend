import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.auth import get_current_admin
from app.db.session import get_db
from app.models.admin import AdminUser
from app.models.send_event import PushSendEvent
from app.schemas.common import PaginatedResponse
from app.schemas.history import SendEventOut

router = APIRouter()


@router.get("", response_model=PaginatedResponse[SendEventOut])
async def list_history(
    target_type: str | None = Query(None),
    dry_run: bool | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> PaginatedResponse[SendEventOut]:
    """Admin: list send events (newest first) with optional filters."""
    query = select(PushSendEvent)
    if target_type is not None:
        query = query.where(PushSendEvent.target_type == target_type)
    if dry_run is not None:
        query = query.where(PushSendEvent.dry_run == dry_run)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    events_result = await db.execute(
        query.order_by(PushSendEvent.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    events = list(events_result.scalars().all())
    return PaginatedResponse(
        items=[SendEventOut.model_validate(e) for e in events],
        total=total, page=page, size=size,
    )


@router.get("/{event_id}", response_model=SendEventOut)
async def get_history_detail(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> SendEventOut:
    """Admin: get a single send event detail."""
    result = await db.execute(select(PushSendEvent).where(PushSendEvent.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return SendEventOut.model_validate(event)
