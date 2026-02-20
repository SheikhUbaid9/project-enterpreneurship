from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_session
from app.schemas.auth import IntrospectRequest, IntrospectResponse, LoginRequest, TokenResponse
from app.schemas.user import UserPublic
from app.services.auth_service import AuthService
from shared.models import Role


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def token_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    service = AuthService(session)
    try:
        return await service.login(email=form_data.username, password=form_data.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    service = AuthService(session)
    try:
        return await service.login(email=payload.email, password=payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/me", response_model=UserPublic)
async def me(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    return user


@router.post("/introspect", response_model=IntrospectResponse)
async def introspect(
    payload: IntrospectRequest,
    session: AsyncSession = Depends(get_session),
) -> IntrospectResponse:
    service = AuthService(session)
    return await service.introspect(payload.token)


@router.get("/roles", response_model=list[str])
async def roles() -> list[str]:
    return [Role.OWNER.value, Role.ADMIN.value, Role.MEMBER.value]


@router.get("/oauth/mock/authorize")
async def oauth_mock_authorize(email: str, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    service = AuthService(session)
    try:
        return await service.issue_token_for_email(email=email)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
