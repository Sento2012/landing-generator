"""Критерий для list-метода — лимит и опциональные фильтры в будущем."""
from pydantic import BaseModel, Field


class GenerationListCriteriaTransfer(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
