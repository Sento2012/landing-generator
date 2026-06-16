"""Вход на регистрацию: email + plaintext-пароль."""
from pydantic import BaseModel, EmailStr, Field


class UserCreateTransfer(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
