from abc import ABC, abstractmethod

from shared.models import Message, PlatformStatus, SendMessageRequest, ThreadDetail


class BaseGatewayPlatformAdapter(ABC):
    platform: str

    @abstractmethod
    async def get_unread_messages(self, token: str, limit: int) -> list[Message]:
        raise NotImplementedError

    @abstractmethod
    async def send_reply(self, token: str, message_id: str, content: str) -> Message:
        raise NotImplementedError

    @abstractmethod
    async def send_message(self, token: str, payload: SendMessageRequest) -> Message:
        raise NotImplementedError

    @abstractmethod
    async def mark_as_read(self, token: str, message_id: str) -> Message:
        raise NotImplementedError

    @abstractmethod
    async def get_platforms(self, token: str) -> list[PlatformStatus]:
        raise NotImplementedError

    @abstractmethod
    async def get_thread(self, token: str, thread_id: str) -> ThreadDetail:
        raise NotImplementedError
