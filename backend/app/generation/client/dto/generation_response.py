"""Ответ GET /api/generations/{id} и POST /api/generations."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GenerationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    status: str
    provider: str
    html: str | None = None
    css: str | None = None
    js: str | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
