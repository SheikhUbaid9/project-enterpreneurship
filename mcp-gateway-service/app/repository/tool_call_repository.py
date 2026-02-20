from redis.asyncio import Redis


class ToolCallRepository:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def log_tool_call(self, tool_name: str, user_id: str, status: str) -> None:
        await self.redis.xadd(
            "tool_calls",
            {
                "tool_name": tool_name,
                "user_id": user_id,
                "status": status,
            },
            maxlen=5000,
            approximate=True,
        )
