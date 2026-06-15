"""Имена доступных LLM-провайдеров. Используются как ключ в реестре плагинов."""
from enum import StrEnum


class LlmProviderName(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
