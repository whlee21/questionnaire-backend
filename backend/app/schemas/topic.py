import uuid
from pydantic import BaseModel


class TopicSubscribeIn(BaseModel):
    topic: str
    tokens: list[str] | None = None
    device_ids: list[uuid.UUID] | None = None


class TopicOut(BaseModel):
    topic: str
    subscriber_count: int
