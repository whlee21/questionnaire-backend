import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.device import Platform


class RegisterDeviceIn(BaseModel):
    fcm_token: str
    platform: Platform
    app_version: str
    installation_id: str | None = None
    external_user_id: str | None = None


class DeviceRegisteredOut(BaseModel):
    id: uuid.UUID
    registered: bool = True


class DeviceOut(BaseModel):
    id: uuid.UUID
    platform: Platform
    app_version: str
    fcm_token_masked: str
    push_enabled: bool
    external_user_id: str | None = None
    last_seen_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
