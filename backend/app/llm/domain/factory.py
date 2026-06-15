"""Factory модуля Llm — хранит реестр плагинов и создаёт сервисы."""
from app.llm.domain.business.plugin_resolver import LlmPluginResolver
from app.llm.domain.models.llm_provider_name import LlmProviderName
from app.llm.domain.plugin.interface import LlmProviderPluginInterface


class LlmFactory:
    def __init__(
        self,
        plugins: dict[LlmProviderName, LlmProviderPluginInterface],
        default: LlmProviderName,
    ) -> None:
        self._plugins = plugins
        self._default = default

    def create_plugin_resolver(self) -> LlmPluginResolver:
        return LlmPluginResolver(plugins=self._plugins, default=self._default)
