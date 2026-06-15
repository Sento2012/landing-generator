"""Внутренняя фабрика Llm-модуля.

Держит реестр доступных плагинов (по одному на провайдера) и default-имя.
Выбор активного плагина — в момент вызова, по имени из LlmPromptTransfer.provider.
"""
from app.llm.domain.plugin.interface import LlmProviderPluginInterface
from app.llm.domain.models.llm_provider_name import LlmProviderName


class LlmFactory:
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

    def get_provider_plugin(
        self,
        name: LlmProviderName | None = None,
    ) -> LlmProviderPluginInterface:
        """Вернуть плагин по имени, либо default если не указан."""
        chosen = name or self._default
        try:
            return self._plugins[chosen]
        except KeyError:
            available = [str(k) for k in self._plugins.keys()]
            raise ValueError(
                f"Unknown LLM provider: {chosen!r}. Available: {available}"
            ) from None
