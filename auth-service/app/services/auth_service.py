from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token, decode_token, verify_password
from app.repository.user_repository import UserRepository
from app.schemas.auth import IntrospectResponse, TokenResponse


settings = get_settings()


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepository(session)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.repo.get_by_email(email=email)
        if user is None or not user.is_active:
            raise ValueError("Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        token = create_access_token(subject=str(user.id), email=user.email, role=user.role)
        return TokenResponse(
            access_token=token,
            expires_in=settings.jwt_expire_minutes * 60,
        )

    async def issue_token_for_email(self, email: str) -> TokenResponse:
        user = await self.repo.get_by_email(email=email)
        if user is None or not user.is_active:
            raise ValueError("Unknown or inactive user")

        token = create_access_token(subject=str(user.id), email=user.email, role=user.role)
        return TokenResponse(
            access_token=token,
            expires_in=settings.jwt_expire_minutes * 60,
        )

    async def introspect(self, token: str) -> IntrospectResponse:
        try:
            payload = decode_token(token)
        except ValueError:
            return IntrospectResponse(active=False)

        user = await self.repo.get_by_id(payload.sub)
        if user is None or not user.is_active:
            return IntrospectResponse(active=False)

        return IntrospectResponse(
            active=True,
            user_id=str(user.id),
            email=user.email,
            role=user.role,
        )
