from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis

from app.core.database import get_redis
from app.dependencies import get_access_token, get_current_user
from app.schemas.rest import (
    MarkReadBody,
    MessageListResponse,
    PlatformsResponse,
    PrioritizeBody,
    SendMessageBody,
    SendReplyBody,
    ThreadResponse,
)
from app.services.mcp_service import MCPService
from shared.models import AuthenticatedUser, SendMessageRequest


router = APIRouter(tags=["gateway"])


@router.get("/messages/unread", response_model=MessageListResponse)
async def get_unread_messages(
    platform: str = Query(default="all"),
    limit: int = Query(default=50, ge=1, le=100),
    token: str = Depends(get_access_token),
    user: AuthenticatedUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> MessageListResponse:
    service = MCPService(redis)
    payload = await service.get_unread_messages(
        token=token,
        user_id=user.user_id,
        platform=platform,
        limit=limit,
    )
    return MessageListResponse(messages=payload["messages"])


@router.post("/messages/{message_id}/reply")
async def send_reply(
    message_id: str,
    body: SendReplyBody,
    token: str = Depends(get_access_token),
    user: AuthenticatedUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> dict:
    service = MCPService(redis)
    payload = await service.send_reply(
        token=token,
        user_id=user.user_id,
        platform=body.platform,
        message_id=message_id,
        content=body.content,
    )
    return {"message": payload}


@router.post("/messages/send")
async def send_message(
    body: SendMessageBody,
    token: str = Depends(get_access_token),
    user: AuthenticatedUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> dict:
    service = MCPService(redis)
    payload = SendMessageRequest(
        platform=body.platform,
        subject=body.subject,
        recipients=body.recipients,
        body=body.body,
        thread_id=body.thread_id,
    )
    message = await service.send_message(
        token=token,
        user_id=user.user_id,
        payload=payload,
        platform=body.platform,
    )
    return {"message": message}


@router.patch("/messages/read")
async def mark_as_read(
    body: MarkReadBody,
    token: str = Depends(get_access_token),
    user: AuthenticatedUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> dict:
    service = MCPService(redis)
    payload = await service.mark_as_read(
        token=token,
        user_id=user.user_id,
        platform=body.platform,
        message_ids=body.message_ids,
    )
    return payload


@router.post("/messages/prioritize")
async def prioritize_messages(
    body: PrioritizeBody,
    user: AuthenticatedUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> dict:
    service = MCPService(redis)
    return await service.prioritize_messages(user_id=user.user_id, messages=body.messages, criteria=body.criteria)


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    platform: str = Query(default="email"),
    token: str = Depends(get_access_token),
    user: AuthenticatedUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> ThreadResponse:
    service = MCPService(redis)
    payload = await service.get_thread(
        token=token,
        user_id=user.user_id,
        platform=platform,
        thread_id=thread_id,
    )
    return ThreadResponse(thread=payload["thread"])


@router.get("/threads/{thread_id}/summary")
async def summarize_thread(
    thread_id: str,
    platform: str = Query(default="email"),
    user: AuthenticatedUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> dict:
    service = MCPService(redis)
    return await service.summarize_threads(user_id=user.user_id, platform=platform, thread_id=thread_id)


@router.get("/messages/search")
async def search_messages(
    q: str = Query(alias="q"),
    platform: str = Query(default="all"),
    user: AuthenticatedUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> dict:
    service = MCPService(redis)
    return await service.search_messages(user_id=user.user_id, platform=platform, query=q)


@router.get("/platforms", response_model=PlatformsResponse)
async def get_platforms(
    token: str = Depends(get_access_token),
    user: AuthenticatedUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> PlatformsResponse:
    service = MCPService(redis)
    payload = await service.get_platforms(token=token, user_id=user.user_id)
    return PlatformsResponse(platforms=payload["platforms"])


# Backward-compatible aliases for current frontend wiring.
@router.get("/v1/inbox/unread", response_model=MessageListResponse)
async def get_unread_messages_v1(
    limit: int = Query(default=50, ge=1, le=100),
    token: str = Depends(get_access_token),
    user: AuthenticatedUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> MessageListResponse:
    service = MCPService(redis)
    payload = await service.get_unread_messages(token=token, user_id=user.user_id, platform="all", limit=limit)
    return MessageListResponse(messages=payload["messages"])


@router.get("/v1/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread_v1(
    thread_id: str,
    token: str = Depends(get_access_token),
    user: AuthenticatedUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> ThreadResponse:
    service = MCPService(redis)
    payload = await service.get_thread(
        token=token,
        user_id=user.user_id,
        platform="email",
        thread_id=thread_id,
    )
    return ThreadResponse(thread=payload["thread"])
