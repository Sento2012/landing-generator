"""Тесты публичных методов LlmFacade.

Facade берёт резолвер из Factory, резолвер выбирает плагин по dto.provider.
Тестируем, что Facade зовёт резолвер с правильным name и проксирует события.
"""
from unittest.mock import MagicMock

import pytest

from app.llm.domain.dto.llm_event import LlmEventTransfer, LlmEventType
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer
from app.llm.domain.facade import LlmFacade
from app.llm.domain.factory import LlmFactory
from app.llm.domain.models.llm_provider_name import LlmProviderName


def _async_gen(events):
    async def gen(prompt):
        for e in events:
            yield e
    return gen


@pytest.fixture
def mock_plugin():
    return MagicMock()


@pytest.fixture
def mock_resolver(mock_plugin):
    resolver = MagicMock()
    resolver.resolve.return_value = mock_plugin
    return resolver


@pytest.fixture
def mock_factory(mock_resolver):
    factory = MagicMock(spec=LlmFactory)
    factory.create_plugin_resolver.return_value = mock_resolver
    return factory


@pytest.fixture
def facade(mock_factory):
    return LlmFacade(mock_factory)


async def test_stream_landing_resolves_by_dto_provider(
    facade, mock_resolver, mock_plugin,
):
    mock_plugin.stream_landing = _async_gen([])

    dto = LlmPromptTransfer(prompt="hi", provider=LlmProviderName.ANTHROPIC)
    _ = [e async for e in facade.stream_landing(dto)]

    mock_resolver.resolve.assert_called_once_with(LlmProviderName.ANTHROPIC)


async def test_stream_landing_resolves_with_none_when_provider_not_set(
    facade, mock_resolver, mock_plugin,
):
    mock_plugin.stream_landing = _async_gen([])

    dto = LlmPromptTransfer(prompt="hi")
    _ = [e async for e in facade.stream_landing(dto)]

    mock_resolver.resolve.assert_called_once_with(None)


async def test_stream_landing_passes_prompt_to_plugin(facade, mock_plugin):
    captured = []

    async def capture(prompt):
        captured.append(prompt)
        if False:
            yield

    mock_plugin.stream_landing = capture

    dto = LlmPromptTransfer(prompt="генерируй лендинг про кофе")
    _ = [e async for e in facade.stream_landing(dto)]

    assert captured == ["генерируй лендинг про кофе"]


async def test_stream_landing_proxies_events(facade, mock_plugin):
    events = [
        LlmEventTransfer(type=LlmEventType.TOOL_START, tool="set_html"),
        LlmEventTransfer(type=LlmEventType.DONE),
    ]
    mock_plugin.stream_landing = _async_gen(events)

    collected = [
        e async for e in facade.stream_landing(LlmPromptTransfer(prompt="x"))
    ]

    assert collected == events
