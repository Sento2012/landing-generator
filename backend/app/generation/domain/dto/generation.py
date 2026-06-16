"""Транспортная модель генерации — что отдаём наружу."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GenerationTransfer(BaseModel):
    """Полное представление генерации (с html/css/js — для GET /{id})."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    prompt: str
    status: str
    provider: str
    html: str | None = None
    css: str | None = None
    js: str | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class GenerationListItemTransfer(BaseModel):
    """Сокращённое — без html/css/js, для GET /."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    prompt: str
    status: str
    provider: str
    created_at: datetime
