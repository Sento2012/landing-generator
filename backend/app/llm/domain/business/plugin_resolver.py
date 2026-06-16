"""Бизнес-логика выбора плагина по имени.

Знает правила:
- None → default.
- Неизвестное имя → ValueError со списком доступных.
- При инициализации проверяет, что default зарегистрирован.
"""
from app.llm.domain.models.llm_provider_name import LlmProviderName
from app.llm.domain.plugin.interface import LlmProviderPluginInterface


class LlmPluginResolver:
    def __init__(
        self,
        plugins: dict[LlmProviderName, LlmProviderPluginInterface],
        default: LlmProviderName,
    ) -> None:
        if default not in plugins:
            raise ValueError(
                f"Default provider {default!r} is not in plugins registry: "
                f"{list(plugins.keys())}"
            )
        self._plugins = plugins
        self._default = default

    def resolve(
        self,
        name: LlmProviderName | None = None,
    ) -> LlmProviderPluginInterface:
        chosen = name or self._default
        try:
            return self._plugins[chosen]
        except KeyError:
            available = [str(k) for k in self._plugins]
            raise ValueError(
                f"Unknown LLM provider: {chosen!r}. Available: {available}"
            ) from None
