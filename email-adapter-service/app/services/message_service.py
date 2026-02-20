from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.gmail_adapter import GmailAdapter
from app.adapters.outlook_adapter import OutlookAdapter
from shared.models import Message, Platform, PlatformStatus, SendMessageRequest, ThreadDetail


class MessageService:
    def __init__(self, session: AsyncSession):
        self.gmail_adapter = GmailAdapter(session)
        self.outlook_adapter = OutlookAdapter()

    async def get_unread_messages(self, user_id: str, limit: int) -> list[Message]:
        return await self.gmail_adapter.fetch_unread(user_id=user_id, limit=limit)

    async def send_reply(self, user_id: str, message_id: str, body: str) -> Message:
        return await self.gmail_adapter.send_reply(user_id=user_id, message_id=message_id, body=body)

    async def send_message(self, user_id: str, payload: SendMessageRequest) -> Message:
        if payload.platform != Platform.EMAIL:
            raise ValueError("Only email platform is supported in email adapter MVP")
        return await self.gmail_adapter.send_message(user_id=user_id, payload=payload)

    async def mark_as_read(self, user_id: str, message_id: str) -> Message:
        return await self.gmail_adapter.mark_as_read(user_id=user_id, message_id=message_id)

    async def get_thread(self, user_id: str, thread_id: str) -> ThreadDetail | None:
        return await self.gmail_adapter.get_thread(user_id=user_id, thread_id=thread_id)

    async def get_platforms(self) -> list[PlatformStatus]:
        return [
            await self.gmail_adapter.get_platform_status(),
            await self.outlook_adapter.get_platform_status(),
        ]
