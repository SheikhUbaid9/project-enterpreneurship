from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from shared.models import AuthenticatedUser, Role


settings = get_settings()


async def introspect_bearer_token(token: str) -> AuthenticatedUser:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.auth_service_url}/auth/introspect",
            json={"token": token},
        )

    if response.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token introspection failed")

    payload: dict[str, Any] = response.json()
    if not payload.get("active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive token")

    return AuthenticatedUser(
        user_id=payload["user_id"],
        email=payload["email"],
        role=Role(payload["role"]),
    )
