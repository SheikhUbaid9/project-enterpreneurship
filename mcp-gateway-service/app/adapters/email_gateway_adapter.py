from app.adapters.base_adapter import BaseGatewayPlatformAdapter
from app.services.email_adapter_client import EmailAdapterClient
from shared.models import Message, PlatformStatus, SendMessageRequest, ThreadDetail


class EmailGatewayAdapter(BaseGatewayPlatformAdapter):
    platform = "email"

    def __init__(self):
        self.client = EmailAdapterClient()

    async def get_unread_messages(self, token: str, limit: int) -> list[Message]:
        return await self.client.get_unread_messages(token=token, limit=limit)

    async def send_reply(self, token: str, message_id: str, content: str) -> Message:
        return await self.client.send_reply(token=token, message_id=message_id, body=content)

    async def send_message(self, token: str, payload: SendMessageRequest) -> Message:
        return await self.client.send_message(token=token, payload=payload)

    async def mark_as_read(self, token: str, message_id: str) -> Message:
        return await self.client.mark_as_read(token=token, message_id=message_id)

    async def get_platforms(self, token: str) -> list[PlatformStatus]:
        return await self.client.get_platforms(token=token)

    async def get_thread(self, token: str, thread_id: str) -> ThreadDetail:
        return await self.client.get_thread(token=token, thread_id=thread_id)
