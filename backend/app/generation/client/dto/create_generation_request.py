"""Тело POST /api/generations."""
from pydantic import BaseModel, Field

from app.llm.domain.models.llm_provider_name import LlmProviderName


class CreateGenerationRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)
    # Какой провайдер использовать. None → server-side default.
    provider: LlmProviderName | None = None
