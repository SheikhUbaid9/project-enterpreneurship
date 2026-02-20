from pydantic import BaseModel, Field

from shared.models import Message, SendMessageRequest, ThreadDetail


class UnreadMessagesResponse(BaseModel):
    messages: list[Message]


class ReplyPayload(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class SendPayload(SendMessageRequest):
    pass


class ThreadResponse(BaseModel):
    thread: ThreadDetail
