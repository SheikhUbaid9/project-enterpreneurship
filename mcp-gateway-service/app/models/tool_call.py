from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class ToolCallLog:
    tool_name: str
    user_id: str
    created_at: datetime = datetime.now(UTC)
