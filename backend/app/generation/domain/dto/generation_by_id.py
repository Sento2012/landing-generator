"""Идентификатор генерации + владелец (для ownership-проверок)."""
from pydantic import BaseModel


class GenerationByIdTransfer(BaseModel):
    id: int
    user_id: int
