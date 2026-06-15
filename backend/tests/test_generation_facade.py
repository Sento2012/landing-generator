"""Тесты публичных методов GenerationFacade.

Facade — тонкая делегирующая оболочка над BusinessFactory.
Тесты проверяют, что:
- В правильный сервис идёт правильный DTO.
- Возврат Facade соответствует контракту (Transfer / Iterator).

Всё ниже Facade (Repository / EntityManager / Generator) — моки.
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.generation.domain.dto.generation import (
    GenerationListItemTransfer,
    GenerationTransfer,
)
from app.generation.domain.dto.generation_by_id import GenerationByIdTransfer
from app.generation.domain.dto.generation_create import GenerationCreateTransfer
from app.generation.domain.dto.generation_list import GenerationListTransfer
from app.generation.domain.dto.generation_list_criteria import (
    GenerationListCriteriaTransfer,
)
from app.generation.domain.facade import GenerationFacade
from app.generation.domain.factory import GenerationFactory
from app.llm.domain.dto.landing_result import LandingResultTransfer
from app.llm.domain.dto.llm_event import LlmEventTransfer, LlmEventType


# ─── Fixtures ────────────────────────────────────────────────────────────────
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
def mock_factory(mock_repository, mock_entity_manager, mock_generator):
    factory = MagicMock(spec=GenerationFactory)
    factory.create_repository.return_value = mock_repository
    factory.create_entity_manager.return_value = mock_entity_manager
    factory.create_generator.return_value = mock_generator
    return factory


@pytest.fixture
def facade(mock_factory):
    return GenerationFacade(mock_factory)


@pytest.fixture
def sample_generation():
    return GenerationTransfer(
        id=42,
        prompt="лендинг про йогу",
        status="completed",
        provider="openai",
        html="<div>...</div>",
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )


# ─── create_generation ───────────────────────────────────────────────────────
async def test_create_generation_delegates_to_entity_manager(
    facade, mock_entity_manager, sample_generation, monkeypatch,
):
    # Мокаем Celery task'у — она вызывается через .delay() после create_*.
    # Реальный broker в тестах не поднят.
    from unittest.mock import MagicMock
    mock_task = MagicMock()
    monkeypatch.setattr(
        "app.generation.domain.business.generation_task.run_generation_task",
        mock_task,
    )

    dto = GenerationCreateTransfer(prompt="лендинг", provider=None)
    mock_entity_manager.create.return_value = sample_generation

    result = await facade.create_generation(dto)

    mock_entity_manager.create.assert_awaited_once_with(dto)
    mock_task.delay.assert_called_once_with(sample_generation.id)
    assert result is sample_generation


# ─── get_generation ──────────────────────────────────────────────────────────
async def test_get_generation_returns_transfer_when_found(
    facade, mock_repository, sample_generation,
):
    mock_repository.find_by_id.return_value = sample_generation

    result = await facade.get_generation(GenerationByIdTransfer(id=42))

    mock_repository.find_by_id.assert_awaited_once_with(42)
    assert result is sample_generation


async def test_get_generation_returns_none_when_not_found(facade, mock_repository):
    mock_repository.find_by_id.return_value = None

    result = await facade.get_generation(GenerationByIdTransfer(id=999))

    assert result is None


# ─── list_generations ────────────────────────────────────────────────────────
async def test_list_generations_wraps_items_in_envelope(facade, mock_repository):
    items = [
        GenerationListItemTransfer(
            id=1,
            prompt="p1",
            status="completed",
            provider="openai",
            created_at=datetime(2026, 1, 1),
        ),
        GenerationListItemTransfer(
            id=2,
            prompt="p2",
            status="pending",
            provider="anthropic",
            created_at=datetime(2026, 1, 2),
        ),
    ]
    mock_repository.list_recent.return_value = items

    result = await facade.list_generations(GenerationListCriteriaTransfer(limit=10))

    mock_repository.list_recent.assert_awaited_once_with(10)
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

    async def fake_stream(gen_id):
        for e in events:
            yield e

    mock_generator.stream = fake_stream

    collected = [e async for e in facade.stream_generation(GenerationByIdTransfer(id=42))]

    assert collected == events


async def test_stream_generation_passes_id_from_dto(facade, mock_generator):
    captured_ids = []

    async def fake_stream(gen_id):
        captured_ids.append(gen_id)
        if False:
            yield  # дам python'у понять что это async-generator

    mock_generator.stream = fake_stream

    _ = [e async for e in facade.stream_generation(GenerationByIdTransfer(id=7))]

    assert captured_ids == [7]
