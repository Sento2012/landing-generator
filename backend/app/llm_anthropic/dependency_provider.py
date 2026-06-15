"""Wiring модуля LlmAnthropic.

Принимает ВСЕ внешние данные параметрами (api_key, model, system_prompt,
tool_descriptions). НЕ читает env и НЕ импортирует конфиги из других модулей.
"""
import anthropic

from app.llm.domain.models.tool_name import LlmToolName
from app.llm_anthropic.domain.business.tools_schema import build_anthropic_tools_schema
from app.llm_anthropic.domain.facade import AnthropicFacade
from app.llm_anthropic.domain.factory import AnthropicFactory
from app.llm_anthropic.domain.plugin.anthropic_provider_plugin import (
    AnthropicProviderPlugin,
)


def build_anthropic_plugin(
    api_key: str,
    model: str,
    system_prompt: str,
    tool_descriptions: dict[LlmToolName, dict[str, str]],
) -> AnthropicProviderPlugin:
    client = anthropic.AsyncAnthropic(api_key=api_key)
    tools = build_anthropic_tools_schema(tool_descriptions)
    factory = AnthropicFactory(
        client=client,
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )
    return AnthropicProviderPlugin(AnthropicFacade(factory))
