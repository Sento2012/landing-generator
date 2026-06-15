"""Тесты публичных методов OpenAiFacade.

Facade берёт сервис из OpenAiFactory и проксирует его поток событий.
"""
from unittest.mock import MagicMock

import pytest

from app.llm.domain.dto.llm_event import LlmEventTransfer, LlmEventType
from app.llm.domain.dto.llm_prompt import LlmPromptTransfer
from app.llm_openai.domain.facade import OpenAiFacade
from app.llm_openai.domain.factory import OpenAiFactory


def _async_gen(events):
    async def gen(dto):
        for e in events:
            yield e
    return gen


@pytest.fixture
def mock_service():
    return MagicMock()


@pytest.fixture
def mock_factory(mock_service):
    factory = MagicMock(spec=OpenAiFactory)
    factory.create_stream_landing_service.return_value = mock_service
    return factory


@pytest.fixture
def facade(mock_factory):
    return OpenAiFacade(mock_factory)


async def test_stream_landing_delegates_to_service(facade, mock_factory, mock_service):
    events = [
        LlmEventTransfer(type=LlmEventType.TOOL_START, tool="set_html"),
        LlmEventTransfer(type=LlmEventType.DONE),
    ]
    mock_service.stream = _async_gen(events)

    dto = LlmPromptTransfer(prompt="x")
    collected = [e async for e in facade.stream_landing(dto)]

    mock_factory.create_stream_landing_service.assert_called_once()
    assert collected == events


async def test_stream_landing_passes_dto_to_service(facade, mock_service):
    captured = []

    async def capture(dto):
        captured.append(dto)
        if False:
            yield

    mock_service.stream = capture

    dto = LlmPromptTransfer(prompt="лендинг про чай")
    _ = [e async for e in facade.stream_landing(dto)]

    assert captured == [dto]
