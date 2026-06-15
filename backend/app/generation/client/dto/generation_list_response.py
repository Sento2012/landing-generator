"""Ответ GET /api/generations с envelope (под total/has_more/cursor в будущем)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GenerationListItemResponse(BaseModel):
    """Один элемент списка (без тяжёлых полей)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    status: str
    provider: str
    created_at: datetime


class GenerationListResponse(BaseModel):
    items: list[GenerationListItemResponse]
