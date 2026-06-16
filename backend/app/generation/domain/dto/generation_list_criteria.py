"""Критерий для list-метода — лимит и владелец (фильтр по owner)."""
from pydantic import BaseModel, Field


class GenerationListCriteriaTransfer(BaseModel):
    user_id: int
    limit: int = Field(default=50, ge=1, le=200)
