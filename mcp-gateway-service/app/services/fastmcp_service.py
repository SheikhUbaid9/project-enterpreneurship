from collections.abc import Callable

from redis.asyncio import Redis

from app.services.mcp_service import MCPService
from shared.models import SendMessageRequest

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - fallback when SDK import fails
    FastMCP = None  # type: ignore


class FastMCPRegistry:
    def __init__(self, redis_provider: Callable[[], Redis]):
        self.redis_provider = redis_provider
        self.server = FastMCP("multi-platform-inbox") if FastMCP else None
        if self.server:
            self._register_tools()

    def _register_tools(self) -> None:
        assert self.server is not None

        @self.server.tool(name="get_unread_messages")
        async def get_unread_messages(access_token: str, user_id: str, platform: str = "all", limit: int = 50) -> dict:
            service = MCPService(self.redis_provider())
            return await service.get_unread_messages(
                token=access_token,
                user_id=user_id,
                platform=platform,
                limit=limit,
            )

        @self.server.tool(name="send_reply")
        async def send_reply(
            access_token: str,
            user_id: str,
            platform: str,
            message_id: str,
            content: str,
        ) -> dict:
            service = MCPService(self.redis_provider())
            return await service.send_reply(
                token=access_token,
                user_id=user_id,
                platform=platform,
                message_id=message_id,
                content=content,
            )

        @self.server.tool(name="send_message")
        async def send_message(
            access_token: str,
            user_id: str,
            platform: str,
            body: str,
            subject: str | None = None,
            recipients: list[str] | None = None,
            thread_id: str | None = None,
        ) -> dict:
            service = MCPService(self.redis_provider())
            payload = SendMessageRequest(
                platform=platform,  # type: ignore[arg-type]
                subject=subject,
                recipients=recipients or [],
                body=body,
                thread_id=thread_id,
            )
            return await service.send_message(
                token=access_token,
                user_id=user_id,
                payload=payload,
                platform=platform,
            )

        @self.server.tool(name="get_platforms")
        async def get_platforms(access_token: str, user_id: str) -> dict:
            service = MCPService(self.redis_provider())
            return await service.get_platforms(token=access_token, user_id=user_id)

        @self.server.tool(name="mark_as_read")
        async def mark_as_read(
            access_token: str,
            user_id: str,
            platform: str,
            message_ids: list[str],
        ) -> dict:
            service = MCPService(self.redis_provider())
            return await service.mark_as_read(
                token=access_token,
                user_id=user_id,
                platform=platform,
                message_ids=message_ids,
            )

        @self.server.tool(name="prioritize_messages")
        async def prioritize_messages(user_id: str, messages: list[dict], criteria: str = "urgency") -> dict:
            service = MCPService(self.redis_provider())
            return await service.prioritize_messages(
                user_id=user_id,
                messages=messages,
                criteria=criteria,
            )

        @self.server.tool(name="summarize_threads")
        async def summarize_threads(user_id: str, platform: str = "email", thread_id: str | None = None) -> dict:
            service = MCPService(self.redis_provider())
            return await service.summarize_threads(user_id=user_id, platform=platform, thread_id=thread_id)

        @self.server.tool(name="search_messages")
        async def search_messages(user_id: str, query: str, platform: str = "all") -> dict:
            service = MCPService(self.redis_provider())
            return await service.search_messages(user_id=user_id, platform=platform, query=query)
