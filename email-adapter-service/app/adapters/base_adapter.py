from abc import ABC, abstractmethod

from shared.models import Message, PlatformStatus, SendMessageRequest, ThreadDetail


class BaseEmailPlatformAdapter(ABC):
    platform_name: str

    @abstractmethod
    async def fetch_unread(self, user_id: str, limit: int) -> list[Message]:
        raise NotImplementedError

    @abstractmethod
    async def send_reply(self, user_id: str, message_id: str, body: str) -> Message:
        raise NotImplementedError

    @abstractmethod
    async def send_message(self, user_id: str, payload: SendMessageRequest) -> Message:
        raise NotImplementedError

    @abstractmethod
    async def mark_as_read(self, user_id: str, message_id: str) -> Message:
        raise NotImplementedError

    @abstractmethod
    async def get_thread(self, user_id: str, thread_id: str) -> ThreadDetail | None:
        raise NotImplementedError

    @abstractmethod
    async def get_platform_status(self) -> PlatformStatus:
        raise NotImplementedError
