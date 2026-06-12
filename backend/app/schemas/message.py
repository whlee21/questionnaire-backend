from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class NotificationPayload(BaseModel):
    title: str
    body: str
    image_url: str | None = None


class TokenTarget(BaseModel):
    type: Literal["token"]
    token: str


class TokensTarget(BaseModel):
    type: Literal["tokens"]
    tokens: list[str] = Field(min_length=1, max_length=500)


class TopicTarget(BaseModel):
    type: Literal["topic"]
    topic: str


class BroadcastTarget(BaseModel):
    type: Literal["broadcast"]


Target = Annotated[
    Union[TokenTarget, TokensTarget, TopicTarget, BroadcastTarget],
    Field(discriminator="type"),
]


class SendRequest(BaseModel):
    target: Target
    notification: NotificationPayload
    data: dict[str, str] = Field(default_factory=dict)
    dry_run: bool = False
    idempotency_key: str | None = None


class SendResultOut(BaseModel):
    success_count: int
    failure_count: int
    invalidated_tokens: list[str] = Field(default_factory=list)
    dry_run: bool
