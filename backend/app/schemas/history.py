import uuid
from datetime import datetime
from pydantic import BaseModel


class SendEventOut(BaseModel):
    id: uuid.UUID
    actor: str
    target_type: str
    target_summary: str
    payload_summary: dict
    dry_run: bool
    success_count: int
    failure_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
