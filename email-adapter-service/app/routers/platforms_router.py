from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_session
from app.schemas.platform import PlatformStatusResponse
from app.services.message_service import MessageService
from shared.models import AuthenticatedUser


router = APIRouter(prefix="/v1", tags=["platforms"])


@router.get("/platforms", response_model=PlatformStatusResponse)
async def get_platforms(
    _: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PlatformStatusResponse:
    service = MessageService(session)
    return PlatformStatusResponse(platforms=await service.get_platforms())
