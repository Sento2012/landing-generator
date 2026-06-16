"""Wiring модуля Llm.

Знает, как собрать LlmFacade из реестра плагинов. Сами плагины приходят
параметром — Llm-модуль не знает про конкретных провайдеров.
"""
from app.llm.domain.facade import LlmFacade
from app.llm.domain.factory import LlmFactory
from app.llm.domain.models.llm_provider_name import LlmProviderName
from app.llm.domain.plugin.interface import LlmProviderPluginInterface


def build_llm_facade(
    plugins: dict[LlmProviderName, LlmProviderPluginInterface],
    default: LlmProviderName,
) -> LlmFacade:
    factory = LlmFactory(plugins=plugins, default=default)
    return LlmFacade(factory)
