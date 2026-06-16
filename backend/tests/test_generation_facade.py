"""Тесты публичных методов GenerationFacade."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.generation.domain.dto.generation import (
    GenerationListItemTransfer,
    GenerationTransfer,
)
from app.generation.domain.dto.generation_by_id import GenerationByIdTransfer
from app.generation.domain.dto.generation_create import GenerationCreateTransfer
from app.generation.domain.dto.generation_execute import GenerationExecuteTransfer
from app.generation.domain.dto.generation_list import GenerationListTransfer
from app.generation.domain.dto.generation_list_criteria import (
    GenerationListCriteriaTransfer,
)
from app.generation.domain.facade import GenerationFacade
from app.generation.domain.factory import GenerationFactory
from app.llm.domain.dto.landing_result import LandingResultTransfer
from app.llm.domain.dto.llm_event import LlmEventTransfer, LlmEventType


@pytest.fixture
def mock_repository():
    return AsyncMock()


@pytest.fixture
def mock_entity_manager():
    return AsyncMock()


@pytest.fixture
def mock_generator():
    return MagicMock()


@pytest.fixture
def mock_scheduler():
    return AsyncMock()


@pytest.fixture
def mock_executor():
    return AsyncMock()


@pytest.fixture
def mock_factory(
    mock_repository, mock_entity_manager, mock_generator, mock_scheduler, mock_executor,
):
    factory = MagicMock(spec=GenerationFactory)
    factory.create_repository.return_value = mock_repository
    factory.create_entity_manager.return_value = mock_entity_manager
    factory.create_generator.return_value = mock_generator
    factory.create_scheduler.return_value = mock_scheduler
    factory.create_executor.return_value = mock_executor
    return factory


@pytest.fixture
def facade(mock_factory):
    return GenerationFacade(mock_factory)


@pytest.fixture
def sample_generation():
    return GenerationTransfer(
        id=42,
        user_id=1,
        prompt="лендинг про йогу",
        status="completed",
        provider="openai",
        html="<div>...</div>",
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )


# ─── create_generation ───────────────────────────────────────────────────────
async def test_create_generation_delegates_to_scheduler(
    facade, mock_scheduler, sample_generation,
):
    dto = GenerationCreateTransfer(prompt="лендинг", provider=None, user_id=1)
    mock_scheduler.schedule.return_value = sample_generation

    result = await facade.create_generation(dto)

    mock_scheduler.schedule.assert_awaited_once_with(dto)
    assert result is sample_generation


# ─── execute_generation ──────────────────────────────────────────────────────
async def test_execute_generation_delegates_to_executor(facade, mock_executor):
    await facade.execute_generation(GenerationExecuteTransfer(id=42))
    mock_executor.execute.assert_awaited_once_with(42)


# ─── get_generation ──────────────────────────────────────────────────────────
async def test_get_generation_returns_transfer_when_found(
    facade, mock_repository, sample_generation,
):
    mock_repository.find_by_id_for_user.return_value = sample_generation

    result = await facade.get_generation(GenerationByIdTransfer(id=42, user_id=1))

    mock_repository.find_by_id_for_user.assert_awaited_once_with(42, 1)
    assert result is sample_generation


async def test_get_generation_returns_none_when_not_found(facade, mock_repository):
    mock_repository.find_by_id_for_user.return_value = None

    result = await facade.get_generation(GenerationByIdTransfer(id=999, user_id=1))

    assert result is None


# ─── list_generations ────────────────────────────────────────────────────────
async def test_list_generations_wraps_items_in_envelope(facade, mock_repository):
    items = [
        GenerationListItemTransfer(
            id=1, user_id=1, prompt="p1", status="completed", provider="openai",
            created_at=datetime(2026, 1, 1),
        ),
        GenerationListItemTransfer(
            id=2, user_id=1, prompt="p2", status="pending", provider="anthropic",
            created_at=datetime(2026, 1, 2),
        ),
    ]
    mock_repository.list_recent_by_user.return_value = items

    result = await facade.list_generations(
        GenerationListCriteriaTransfer(user_id=1, limit=10)
    )

    mock_repository.list_recent_by_user.assert_awaited_once_with(1, 10)
    assert isinstance(result, GenerationListTransfer)
    assert result.items == items


# ─── stream_generation ───────────────────────────────────────────────────────
async def test_stream_generation_yields_events_from_generator(facade, mock_generator):
    events = [
        LlmEventTransfer(type=LlmEventType.TOOL_START, tool="set_html"),
        LlmEventTransfer(
            type=LlmEventType.DONE,
            result=LandingResultTransfer(html="<h1>hi</h1>", css="", js=""),
        ),
    ]

    async def fake_stream(dto):
        for e in events:
            yield e

    mock_generator.stream = fake_stream

    collected = [
        e async for e in facade.stream_generation(
            GenerationByIdTransfer(id=42, user_id=1)
        )
    ]
    assert collected == events


async def test_stream_generation_passes_dto_with_user(facade, mock_generator):
    captured = []

    async def fake_stream(dto):
        captured.append(dto)
        if False:
            yield

    mock_generator.stream = fake_stream

    _ = [
        e async for e in facade.stream_generation(
            GenerationByIdTransfer(id=7, user_id=99)
        )
    ]

    assert len(captured) == 1
    assert captured[0].id == 7
    assert captured[0].user_id == 99
