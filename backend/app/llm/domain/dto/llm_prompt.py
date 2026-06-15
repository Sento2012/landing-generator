"""Вход для LlmFacade.stream_landing — промпт + выбор провайдера."""
from pydantic import BaseModel, Field

from app.llm.domain.models.llm_provider_name import LlmProviderName


class LlmPromptTransfer(BaseModel):
    prompt: str = Field(min_length=1)
    # None → используется default из LlmFactory
    provider: LlmProviderName | None = None
