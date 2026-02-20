from app.adapters.base_adapter import BaseEmailPlatformAdapter
from shared.models import Message, Platform, PlatformStatus, SendMessageRequest, ThreadDetail


class OutlookAdapter(BaseEmailPlatformAdapter):
    platform_name = "outlook"

    async def fetch_unread(self, user_id: str, limit: int) -> list[Message]:
        return []

    async def send_reply(self, user_id: str, message_id: str, body: str) -> Message:
        raise ValueError("Outlook adapter is not enabled in MVP")

    async def send_message(self, user_id: str, payload: SendMessageRequest) -> Message:
        raise ValueError("Outlook adapter is not enabled in MVP")

    async def mark_as_read(self, user_id: str, message_id: str) -> Message:
        raise ValueError("Outlook adapter is not enabled in MVP")

    async def get_thread(self, user_id: str, thread_id: str) -> ThreadDetail | None:
        return None

    async def get_platform_status(self) -> PlatformStatus:
        return PlatformStatus(
            platform=Platform.EMAIL,
            connected=False,
            status="planned",
            detail="Outlook Graph adapter planned for phase 2.",
        )
