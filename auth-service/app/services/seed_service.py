from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password
from app.repository.user_repository import UserRepository
from shared.constants import DEFAULT_ADMIN_USER_ID, DEFAULT_MEMBER_USER_ID, DEFAULT_OWNER_USER_ID
from shared.models import Role


settings = get_settings()


async def seed_users(session: AsyncSession) -> None:
    repo = UserRepository(session)
    seed_data = [
        (
            DEFAULT_OWNER_USER_ID,
            settings.seed_owner_email,
            settings.seed_owner_password,
            Role.OWNER.value,
        ),
        (
            DEFAULT_ADMIN_USER_ID,
            settings.seed_admin_email,
            settings.seed_admin_password,
            Role.ADMIN.value,
        ),
        (
            DEFAULT_MEMBER_USER_ID,
            settings.seed_member_email,
            settings.seed_member_password,
            Role.MEMBER.value,
        ),
    ]

    for user_id, email, password, role in seed_data:
        existing = await repo.get_by_email(email)
        if existing:
            continue
        await repo.create_user(email=email, password_hash=hash_password(password), role=role, user_id=user_id)

    await session.commit()
