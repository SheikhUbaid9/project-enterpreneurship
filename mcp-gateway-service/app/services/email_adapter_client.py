from typing import Any

import httpx

from app.core.config import get_settings
from shared.models import Message, PlatformStatus, SendMessageRequest, ThreadDetail


settings = get_settings()


class EmailAdapterClient:
    def __init__(self):
        self.base_url = settings.email_adapter_url

    async def _request(
        self,
        method: str,
        path: str,
        token: str,
        json_payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.request(
                method=method,
                url=f"{self.base_url}{path}",
                json=json_payload,
                params=params,
                headers=headers,
            )
        response.raise_for_status()
        return response.json()

    async def get_unread_messages(self, token: str, limit: int = 25) -> list[Message]:
        payload = await self._request("GET", "/v1/messages/unread", token=token, params={"limit": limit})
        return [Message(**message) for message in payload["messages"]]

    async def send_reply(self, token: str, message_id: str, body: str) -> Message:
        payload = await self._request(
            "POST",
            f"/v1/messages/{message_id}/reply",
            token=token,
            json_payload={"body": body},
        )
        return Message(**payload)

    async def send_message(self, token: str, payload: SendMessageRequest) -> Message:
        message = await self._request(
            "POST",
            "/v1/messages/send",
            token=token,
            json_payload=payload.model_dump(),
        )
        return Message(**message)

    async def mark_as_read(self, token: str, message_id: str) -> Message:
        payload = await self._request(
            "POST",
            f"/v1/messages/{message_id}/mark-read",
            token=token,
        )
        return Message(**payload)

    async def get_thread(self, token: str, thread_id: str) -> ThreadDetail:
        payload = await self._request("GET", f"/v1/threads/{thread_id}", token=token)
        return ThreadDetail(**payload["thread"])

    async def get_platforms(self, token: str) -> list[PlatformStatus]:
        payload = await self._request("GET", "/v1/platforms", token=token)
        return [PlatformStatus(**platform) for platform in payload["platforms"]]
