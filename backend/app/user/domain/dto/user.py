"""Business Transfer для User — публичные данные (без password_hash)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserTransfer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime
