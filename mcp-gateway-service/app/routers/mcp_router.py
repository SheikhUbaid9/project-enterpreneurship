import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.database import get_redis
from app.core.security import introspect_bearer_token
from app.services.mcp_service import MCPService
from shared.jsonrpc import JsonRpcError, JsonRpcRequest, JsonRpcResponse
from shared.models import SendMessageRequest


router = APIRouter(prefix="/mcp", tags=["mcp"])
settings = get_settings()


TOOL_DEFINITIONS = [
    {
        "name": "get_unread_messages",
        "description": "Fetch unread messages from one platform or all adapters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "default": "all"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
            },
        },
    },
    {
        "name": "send_reply",
        "description": "Send a reply to a message through the selected platform adapter.",
        "inputSchema": {
            "type": "object",
            "required": ["platform", "message_id", "content"],
            "properties": {
                "platform": {"type": "string"},
                "message_id": {"type": "string"},
                "content": {"type": "string"},
            },
        },
    },
    {
        "name": "send_message",
        "description": "Send a new outbound message.",
        "inputSchema": {
            "type": "object",
            "required": ["platform", "body"],
            "properties": {
                "platform": {"type": "string"},
                "thread_id": {"type": "string"},
                "subject": {"type": "string"},
                "recipients": {"type": "array", "items": {"type": "string"}},
                "body": {"type": "string"},
            },
        },
    },
    {
        "name": "get_platforms",
        "description": "Get platform status from all adapters.",
        "inputSchema": {"type": "object"},
    },
    {
        "name": "mark_as_read",
        "description": "Mark messages as read on a selected platform.",
        "inputSchema": {
            "type": "object",
            "required": ["platform", "message_ids"],
            "properties": {
                "platform": {"type": "string"},
                "message_ids": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    {
        "name": "prioritize_messages",
        "description": "Sort messages by urgency/importance criteria.",
        "inputSchema": {
            "type": "object",
            "required": ["messages"],
            "properties": {
                "messages": {"type": "array", "items": {"type": "object"}},
                "criteria": {"type": "string", "default": "urgency"},
            },
        },
    },
    {
        "name": "summarize_threads",
        "description": "Phase 2 placeholder for thread summarization.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "thread_id": {"type": "string"},
                "platform": {"type": "string", "default": "email"},
            },
        },
    },
    {
        "name": "search_messages",
        "description": "Phase 3 placeholder for cross-platform search.",
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string"},
                "platform": {"type": "string", "default": "all"},
            },
        },
    },
]


def _ok(request_id: str | int | None, result: Any) -> JsonRpcResponse:
    return JsonRpcResponse(id=request_id, result=result)


def _fail(request_id: str | int | None, code: int, message: str, data: Any = None) -> JsonRpcResponse:
    return JsonRpcResponse(id=request_id, error=JsonRpcError(code=code, message=message, data=data))


async def _resolve_user(authorization: str | None) -> tuple[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    user = await introspect_bearer_token(token)
    return token, user.user_id


async def _dispatch_tool(
    service: MCPService,
    token: str,
    user_id: str,
    tool_name: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    if tool_name == "get_unread_messages":
        return await service.get_unread_messages(
            token=token,
            user_id=user_id,
            platform=str(args.get("platform", "all")),
            limit=int(args.get("limit", 50)),
        )
    if tool_name == "send_reply":
        return await service.send_reply(
            token=token,
            user_id=user_id,
            platform=str(args.get("platform", "email")),
            message_id=str(args.get("message_id", "")),
            content=str(args.get("content", "")),
        )
    if tool_name == "send_message":
        payload = SendMessageRequest(
            platform=str(args.get("platform", "email")),  # type: ignore[arg-type]
            thread_id=args.get("thread_id"),
            subject=args.get("subject"),
            recipients=[str(item) for item in args.get("recipients", [])],
            body=str(args.get("body", "")),
        )
        return await service.send_message(
            token=token,
            user_id=user_id,
            payload=payload,
            platform=str(args.get("platform", "email")),
        )
    if tool_name == "get_platforms":
        return await service.get_platforms(token=token, user_id=user_id)
    if tool_name == "mark_as_read":
        message_ids = [str(item) for item in args.get("message_ids", [])]
        return await service.mark_as_read(
            token=token,
            user_id=user_id,
            platform=str(args.get("platform", "email")),
            message_ids=message_ids,
        )
    if tool_name == "prioritize_messages":
        messages = args.get("messages", [])
        if not isinstance(messages, list):
            raise ValueError("messages must be a list")
        return await service.prioritize_messages(
            user_id=user_id,
            messages=[item for item in messages if isinstance(item, dict)],
            criteria=str(args.get("criteria", "urgency")),
        )
    if tool_name == "summarize_threads":
        return await service.summarize_threads(
            user_id=user_id,
            platform=str(args.get("platform", "email")),
            thread_id=args.get("thread_id"),
        )
    if tool_name == "search_messages":
        return await service.search_messages(
            user_id=user_id,
            platform=str(args.get("platform", "all")),
            query=str(args.get("query", "")),
        )
    raise ValueError(f"Unknown tool: {tool_name}")


@router.post("")
async def mcp_jsonrpc(
    request: JsonRpcRequest,
    redis: Redis = Depends(get_redis),
    authorization: str | None = Header(default=None),
) -> JsonRpcResponse:
    if request.jsonrpc != "2.0":
        return _fail(request.id, -32600, "Invalid Request")

    if request.method == "initialize":
        return _ok(
            request.id,
            {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "Multi-Platform Inbox MCP Gateway", "version": "1.0.0"},
                "capabilities": {"tools": {}},
            },
        )

    if request.method == "tools/list":
        return _ok(request.id, {"tools": TOOL_DEFINITIONS})

    if request.method == "ping":
        return _ok(request.id, {"status": "pong"})

    try:
        token, user_id = await _resolve_user(authorization)
    except HTTPException:
        return _fail(request.id, -32001, "Unauthorized")

    service = MCPService(redis)
    try:
        if request.method == "tools/call":
            tool_name = str(request.params.get("name", ""))
            args = request.params.get("arguments", {})
            if not isinstance(args, dict):
                return _fail(request.id, -32602, "Invalid params", {"arguments": "Expected object"})
            result = await _dispatch_tool(service, token, user_id, tool_name, args)
        else:
            result = await _dispatch_tool(service, token, user_id, request.method, request.params)
    except ValueError as exc:
        return _fail(request.id, -32601, str(exc))
    except HTTPException as exc:
        return _fail(request.id, -32000, "Tool execution failed", {"detail": exc.detail})
    except Exception as exc:  # pragma: no cover
        return _fail(request.id, -32000, "Tool execution failed", {"error": str(exc)})

    return _ok(request.id, result)


@router.get("/sse")
async def mcp_sse(
    redis: Redis = Depends(get_redis),
    authorization: str | None = Header(default=None),
) -> StreamingResponse:
    token, user_id = await _resolve_user(authorization)
    service = MCPService(redis)

    async def event_stream():
        stream_id = "$"
        while True:
            unread = await service.get_unread_messages(token=token, user_id=user_id, platform="all", limit=5)
            yield f"event: unread_snapshot\ndata: {json.dumps(unread)}\n\n"

            entries = await redis.xread({"tool_calls": stream_id}, count=10, block=1000)
            for _, stream_entries in entries:
                for event_id, data in stream_entries:
                    stream_id = event_id
                    yield f"event: tool_call\ndata: {json.dumps(data)}\n\n"

            yield "event: heartbeat\ndata: {}\n\n"
            await asyncio.sleep(settings.mcp_sse_heartbeat_seconds)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
