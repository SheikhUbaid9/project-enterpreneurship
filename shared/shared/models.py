from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Platform(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    WHATSAPP = "whatsapp"


class Priority(str, Enum):
    URGENT = "urgent"
    NORMAL = "normal"
    LOW = "low"


class MessageDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str
    role: Role


class Message(BaseModel):
    id: str
    thread_id: str
    user_id: str
    platform: Platform
    sender: str
    recipients: list[str] = Field(default_factory=list)
    subject: str | None = None
    body: str
    is_unread: bool
    direction: MessageDirection
    priority: Priority = Priority.NORMAL
    sent_at: datetime


class ThreadDetail(BaseModel):
    id: str
    user_id: str
    platform: Platform
    subject: str | None = None
    participants: list[str] = Field(default_factory=list)
    unread_count: int = 0
    messages: list[Message] = Field(default_factory=list)


class PlatformStatus(BaseModel):
    platform: Platform
    connected: bool
    status: str
    detail: str | None = None


class ReplyRequest(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class SendMessageRequest(BaseModel):
    platform: Platform = Platform.EMAIL
    subject: str | None = None
    recipients: list[str] = Field(default_factory=list)
    body: str = Field(min_length=1, max_length=5000)
    thread_id: str | None = None


class ToolCallResponse(BaseModel):
    ok: bool = True
    data: dict | list | str | None = None
    message: str | None = None
