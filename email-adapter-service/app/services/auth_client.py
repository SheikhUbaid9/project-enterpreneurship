from typing import Any

import httpx

from app.core.config import get_settings
from shared.models import AuthenticatedUser, Role


settings = get_settings()


async def introspect_token(token: str) -> AuthenticatedUser:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.auth_service_url}/auth/introspect",
            json={"token": token},
        )
    response.raise_for_status()
    payload: dict[str, Any] = response.json()
    if not payload.get("active"):
        raise ValueError("Inactive token")

    return AuthenticatedUser(
        user_id=payload["user_id"],
        email=payload["email"],
        role=Role(payload["role"]),
    )
