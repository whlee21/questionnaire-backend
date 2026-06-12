from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_admin
from app.db.session import get_db
from app.models.admin import AdminUser
from app.schemas.message import SendRequest, SendResultOut
from app.services.fcm import FcmClient, get_fcm_client
from app.services.sender import send_notification

router = APIRouter()
_limiter = Limiter(key_func=get_remote_address)


@router.post("/send", response_model=SendResultOut)
@_limiter.limit("30/minute")
async def send_message(
    request: Request,
    body: SendRequest,
    db: AsyncSession = Depends(get_db),
    fcm: FcmClient = Depends(get_fcm_client),
    admin: AdminUser = Depends(get_current_admin),
) -> SendResultOut:
    return await send_notification(db=db, fcm=fcm, request=body, actor=admin.email)
