"""Креды для логина."""
from pydantic import BaseModel, EmailStr


class UserCredentialsTransfer(BaseModel):
    email: EmailStr
    password: str
