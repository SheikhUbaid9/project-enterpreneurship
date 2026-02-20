from pydantic import BaseModel

from shared.models import PlatformStatus


class PlatformStatusResponse(BaseModel):
    platforms: list[PlatformStatus]
