from datetime import datetime

from pydantic import BaseModel

from shared.models import Role


class UserPublic(BaseModel):
    id: str
    email: str
    role: Role
    is_active: bool
    created_at: datetime
