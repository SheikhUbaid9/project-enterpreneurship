from fastapi import HTTPException, status

from app.adapters.base_adapter import BaseGatewayPlatformAdapter
from shared.models import Message, Platform, PlatformStatus, SendMessageRequest, ThreadDetail


class WhatsAppGatewayAdapter(BaseGatewayPlatformAdapter):
    platform = "whatsapp"

    async def get_unread_messages(self, token: str, limit: int) -> list[Message]:
        return []

    async def send_reply(self, token: str, message_id: str, content: str) -> Message:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WhatsApp adapter is a stub in v1 MVP.",
        )

    async def send_message(self, token: str, payload: SendMessageRequest) -> Message:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WhatsApp adapter is a stub in v1 MVP.",
        )

    async def mark_as_read(self, token: str, message_id: str) -> Message:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WhatsApp adapter is a stub in v1 MVP.",
        )

    async def get_platforms(self, token: str) -> list[PlatformStatus]:
        return [
            PlatformStatus(
                platform=Platform.WHATSAPP,
                connected=False,
                status="stub",
                detail="WhatsApp adapter service stub available on port 8004.",
            )
        ]

    async def get_thread(self, token: str, thread_id: str) -> ThreadDetail:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WhatsApp adapter is a stub in v1 MVP.",
        )
