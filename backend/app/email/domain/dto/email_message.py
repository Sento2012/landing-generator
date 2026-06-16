"""DTO для одного email-сообщения."""
from pydantic import BaseModel, EmailStr, Field


class EmailMessageTransfer(BaseModel):
    to: EmailStr
    subject: str = Field(min_length=1, max_length=500)
    body: str
