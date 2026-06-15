"""Wiring модуля LlmOpenAi.

Принимает ВСЕ внешние данные параметрами. НЕ читает env и НЕ импортирует конфиги.
"""
from openai import AsyncOpenAI

from app.llm.domain.models.tool_name import LlmToolName
from app.llm_openai.domain.business.tools_schema import build_openai_tools_schema
from app.llm_openai.domain.facade import OpenAiFacade
from app.llm_openai.domain.factory import OpenAiFactory
from app.llm_openai.domain.plugin.openai_provider_plugin import OpenAiProviderPlugin


def build_openai_plugin(
    api_key: str,
    model: str,
    system_prompt: str,
    tool_descriptions: dict[LlmToolName, dict[str, str]],
) -> OpenAiProviderPlugin:
    client = AsyncOpenAI(api_key=api_key)
    tools = build_openai_tools_schema(tool_descriptions)
    factory = OpenAiFactory(
        client=client,
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )
    return OpenAiProviderPlugin(OpenAiFacade(factory))
