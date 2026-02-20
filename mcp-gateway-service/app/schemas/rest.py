from typing import Literal

from pydantic import BaseModel, Field

from shared.models import Message, PlatformStatus, SendMessageRequest, ThreadDetail


class MessageListResponse(BaseModel):
    messages: list[Message]


class ThreadResponse(BaseModel):
    thread: ThreadDetail


class SendReplyBody(BaseModel):
    platform: Literal["email", "slack", "whatsapp"] = Field(default="email")
    content: str = Field(min_length=1, max_length=5000)


class SendMessageBody(BaseModel):
    platform: Literal["email", "slack", "whatsapp"] = Field(default="email")
    subject: str | None = None
    recipients: list[str] = Field(default_factory=list)
    body: str = Field(min_length=1, max_length=5000)
    thread_id: str | None = None


class MarkReadBody(BaseModel):
    platform: Literal["email", "slack", "whatsapp"] = Field(default="email")
    message_ids: list[str] = Field(min_length=1)


class PrioritizeBody(BaseModel):
    messages: list[dict]
    criteria: str = Field(default="urgency")


class PlatformsResponse(BaseModel):
    platforms: list[PlatformStatus]
