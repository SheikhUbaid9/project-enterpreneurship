from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session, require_roles
from app.repository.user_repository import UserRepository
from app.schemas.user import UserPublic
from shared.models import Role


router = APIRouter(prefix="/auth", tags=["users"])


@router.get("/users", response_model=list[UserPublic])
async def list_users(
    _: UserPublic = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> list[UserPublic]:
    repo = UserRepository(session)
    users = await repo.list_users()
    return [
        UserPublic(
            id=str(user.id),
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        for user in users
    ]
