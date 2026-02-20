import asyncio
from collections import defaultdict

from fastapi import HTTPException, status
from redis.asyncio import Redis

from app.adapters.factory import AdapterFactory
from app.repository.tool_call_repository import ToolCallRepository
from shared.models import SendMessageRequest


class MCPService:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.tool_repo = ToolCallRepository(redis)
        self.adapter_factory = AdapterFactory()

    async def get_unread_messages(
        self,
        token: str,
        user_id: str,
        platform: str = "all",
        limit: int = 50,
    ) -> dict:
        adapters = self._resolve_adapters(platform)
        if platform == "all":
            results = await asyncio.gather(
                *[adapter.get_unread_messages(token=token, limit=limit) for adapter in adapters]
            )
            messages = [message for adapter_messages in results for message in adapter_messages]
        else:
            messages = await adapters[0].get_unread_messages(token=token, limit=limit)

        await self.tool_repo.log_tool_call("get_unread_messages", user_id, "success")
        return {"messages": [message.model_dump(mode="json") for message in messages]}

    async def send_reply(
        self,
        token: str,
        user_id: str,
        platform: str,
        message_id: str,
        content: str,
    ) -> dict:
        adapter = self.adapter_factory.get(platform)
        message = await adapter.send_reply(token=token, message_id=message_id, content=content)
        await self.tool_repo.log_tool_call("send_reply", user_id, "success")
        return message.model_dump(mode="json")

    async def send_message(
        self,
        token: str,
        user_id: str,
        payload: SendMessageRequest,
        platform: str,
    ) -> dict:
        adapter = self.adapter_factory.get(platform)
        message = await adapter.send_message(token=token, payload=payload)
        await self.tool_repo.log_tool_call("send_message", user_id, "success")
        return message.model_dump(mode="json")

    async def mark_as_read(
        self,
        token: str,
        user_id: str,
        platform: str,
        message_ids: list[str],
    ) -> dict:
        adapter = self.adapter_factory.get(platform)
        updated: list[dict] = []
        for message_id in message_ids:
            updated_message = await adapter.mark_as_read(token=token, message_id=message_id)
            updated.append(updated_message.model_dump(mode="json"))
        await self.tool_repo.log_tool_call("mark_as_read", user_id, "success")
        return {"messages": updated}

    async def get_platforms(self, token: str, user_id: str) -> dict:
        statuses = await asyncio.gather(
            *[adapter.get_platforms(token=token) for adapter in self.adapter_factory.all()]
        )
        merged = [item.model_dump(mode="json") for sublist in statuses for item in sublist]
        # Deduplicate by platform + status to avoid duplicate email rows from adapters that represent email channels.
        deduped = []
        seen = set()
        for item in merged:
            key = (item["platform"], item["status"], item.get("detail"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        await self.tool_repo.log_tool_call("get_platforms", user_id, "success")
        return {"platforms": deduped}

    async def get_thread(self, token: str, user_id: str, platform: str, thread_id: str) -> dict:
        adapter = self.adapter_factory.get(platform)
        thread = await adapter.get_thread(token=token, thread_id=thread_id)
        await self.tool_repo.log_tool_call("get_thread", user_id, "success")
        return {"thread": thread.model_dump(mode="json")}

    async def prioritize_messages(self, user_id: str, messages: list[dict], criteria: str = "urgency") -> dict:
        ranked_messages = sorted(
            messages,
            key=lambda item: self._priority_rank(str(item.get("priority", "normal"))),
        )
        await self.tool_repo.log_tool_call("prioritize_messages", user_id, "success")
        return {
            "criteria": criteria,
            "messages": ranked_messages,
        }

    async def summarize_threads(self, user_id: str, platform: str, thread_id: str | None = None) -> dict:
        await self.tool_repo.log_tool_call("summarize_threads", user_id, "not_implemented")
        return {
            "phase": 2,
            "platform": platform,
            "thread_id": thread_id,
            "summary": "Thread summarization integration is planned for phase 2.",
        }

    async def search_messages(self, user_id: str, platform: str, query: str) -> dict:
        await self.tool_repo.log_tool_call("search_messages", user_id, "not_implemented")
        return {
            "phase": 3,
            "platform": platform,
            "query": query,
            "result": "Search service is planned for phase 3.",
        }

    def _resolve_adapters(self, platform: str):
        if platform == "all":
            return self.adapter_factory.all()
        return [self.adapter_factory.get(platform)]

    @staticmethod
    def _priority_rank(priority: str) -> int:
        order = defaultdict(lambda: 99, {"urgent": 0, "normal": 1, "low": 2})
        return order[priority]
