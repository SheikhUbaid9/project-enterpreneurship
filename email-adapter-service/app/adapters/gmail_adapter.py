from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base_adapter import BaseEmailPlatformAdapter
from app.repository.message_repository import MessageRepository
from shared.models import Message, Platform, PlatformStatus, SendMessageRequest, ThreadDetail


class GmailAdapter(BaseEmailPlatformAdapter):
    platform_name = "gmail"

    def __init__(self, session: AsyncSession):
        self.repo = MessageRepository(session)

    async def fetch_unread(self, user_id: str, limit: int) -> list[Message]:
        return await self.repo.get_unread_messages(user_id=user_id, limit=limit)

    async def send_reply(self, user_id: str, message_id: str, body: str) -> Message:
        return await self.repo.send_reply(user_id=user_id, message_id=message_id, body=body)

    async def send_message(self, user_id: str, payload: SendMessageRequest) -> Message:
        return await self.repo.send_message(
            user_id=user_id,
            subject=payload.subject,
            recipients=payload.recipients,
            body=payload.body,
            thread_id=payload.thread_id,
        )

    async def mark_as_read(self, user_id: str, message_id: str) -> Message:
        return await self.repo.mark_as_read(user_id=user_id, message_id=message_id)

    async def get_thread(self, user_id: str, thread_id: str) -> ThreadDetail | None:
        return await self.repo.get_thread(user_id=user_id, thread_id=thread_id)

    async def get_platform_status(self) -> PlatformStatus:
        return PlatformStatus(
            platform=Platform.EMAIL,
            connected=True,
            status="healthy",
            detail="Gmail mock adapter ready",
        )
