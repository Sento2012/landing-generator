"""Вход на создание генерации — то, что зовущий передаёт в Facade."""
from pydantic import BaseModel, Field

from app.llm.domain.models.llm_provider_name import LlmProviderName


class GenerationCreateTransfer(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)
    # Какой провайдер использовать. None → default из конфигурации.
    provider: LlmProviderName | None = None
    # Владелец — приходит из JWT в контроллере, не из тела HTTP-запроса.
    user_id: int
