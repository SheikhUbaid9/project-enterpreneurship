from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_session
from app.schemas.message import ReplyPayload, SendPayload, ThreadResponse, UnreadMessagesResponse
from app.services.message_service import MessageService
from shared.models import AuthenticatedUser, Message, SendMessageRequest


router = APIRouter(prefix="/v1", tags=["messages"])


@router.get("/messages/unread", response_model=UnreadMessagesResponse)
async def get_unread_messages(
    limit: int = Query(default=25, ge=1, le=100),
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UnreadMessagesResponse:
    service = MessageService(session)
    messages = await service.get_unread_messages(user_id=user.user_id, limit=limit)
    return UnreadMessagesResponse(messages=messages)


@router.post("/messages/{message_id}/reply", response_model=Message)
async def send_reply(
    message_id: str,
    payload: ReplyPayload,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Message:
    service = MessageService(session)
    try:
        return await service.send_reply(user_id=user.user_id, message_id=message_id, body=payload.body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/messages/send", response_model=Message)
async def send_message(
    payload: SendPayload,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Message:
    service = MessageService(session)
    request = SendMessageRequest(**payload.model_dump())
    try:
        return await service.send_message(user_id=user.user_id, payload=request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/messages/{message_id}/mark-read", response_model=Message)
async def mark_as_read(
    message_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Message:
    service = MessageService(session)
    try:
        return await service.mark_as_read(user_id=user.user_id, message_id=message_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ThreadResponse:
    service = MessageService(session)
    thread = await service.get_thread(user_id=user.user_id, thread_id=thread_id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return ThreadResponse(thread=thread)
