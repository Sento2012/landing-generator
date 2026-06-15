"""Тесты HTTP endpoints (Generation controller + /health).

Facade подменяется через app.dependency_overrides — реальный LLM/БД не дёргаются.
TestClient создаётся БЕЗ `with` — lifespan не запускается, БД не нужна.

Что проверяем для каждого endpoint:
- Статус-код ответа.
- Контракт ответа (поля, типы, схема).
- Контракт запроса (валидация ошибочного body → 422).
- Маппинг Client DTO ↔ Business Transfer (что Facade зовётся с правильным DTO).
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.generation.domain.dto.generation import (
    GenerationListItemTransfer,
    GenerationTransfer,
)
from app.generation.domain.dto.generation_create import GenerationCreateTransfer
from app.generation.domain.dto.generation_list import GenerationListTransfer
from app.llm.domain.dto.landing_result import LandingResultTransfer
from app.llm.domain.dto.llm_event import LlmEventTransfer, LlmEventType
from app.main import app
from app.shared.dependency_provider import get_generation_facade


# ─── Fixtures ────────────────────────────────────────────────────────────────
@pytest.fixture
def mock_facade():
    facade = MagicMock()
    facade.create_generation = AsyncMock()
    facade.get_generation = AsyncMock()
    facade.list_generations = AsyncMock()
    # stream_generation — async generator, не AsyncMock
    return facade


@pytest.fixture
def client(mock_facade):
    app.dependency_overrides[get_generation_facade] = lambda: mock_facade
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_generation():
    return GenerationTransfer(
        id=42,
        prompt="лендинг про йогу",
        status="completed",
        provider="openai",
        html="<h1>Yoga</h1>",
        css=".hero{}",
        js="",
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        completed_at=datetime(2026, 1, 1, 12, 0, 30),
    )


# ─── Health ──────────────────────────────────────────────────────────────────
def test_health_returns_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ─── POST /api/generations ───────────────────────────────────────────────────
def test_create_generation_returns_201(client, mock_facade, sample_generation):
    mock_facade.create_generation.return_value = sample_generation

    r = client.post("/api/generations", json={"prompt": "лендинг про йогу"})

    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 42
    assert body["status"] == "completed"
    assert body["provider"] == "openai"


def test_create_generation_passes_dto_to_facade(client, mock_facade, sample_generation):
    mock_facade.create_generation.return_value = sample_generation

    client.post("/api/generations", json={"prompt": "test", "provider": "anthropic"})

    mock_facade.create_generation.assert_awaited_once()
    business_dto = mock_facade.create_generation.await_args.args[0]
    assert isinstance(business_dto, GenerationCreateTransfer)
    assert business_dto.prompt == "test"
    assert str(business_dto.provider) == "anthropic"


def test_create_generation_rejects_short_prompt(client):
    r = client.post("/api/generations", json={"prompt": "hi"})  # < 3 chars
    assert r.status_code == 422


def test_create_generation_rejects_unknown_provider(client):
    r = client.post("/api/generations", json={"prompt": "test", "provider": "gpt-4"})
    assert r.status_code == 422


# ─── GET /api/generations ────────────────────────────────────────────────────
def test_list_generations_returns_envelope(client, mock_facade):
    mock_facade.list_generations.return_value = GenerationListTransfer(
        items=[
            GenerationListItemTransfer(
                id=1, prompt="p1", status="completed", provider="openai",
                created_at=datetime(2026, 1, 1),
            ),
            GenerationListItemTransfer(
                id=2, prompt="p2", status="pending", provider="anthropic",
                created_at=datetime(2026, 1, 2),
            ),
        ]
    )

    r = client.get("/api/generations")

    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert len(body["items"]) == 2
    assert body["items"][0]["id"] == 1
    assert body["items"][1]["provider"] == "anthropic"


def test_list_generations_uses_default_limit(client, mock_facade):
    mock_facade.list_generations.return_value = GenerationListTransfer(items=[])

    client.get("/api/generations")

    business_dto = mock_facade.list_generations.await_args.args[0]
    assert business_dto.limit == 50  # default


def test_list_generations_passes_custom_limit(client, mock_facade):
    mock_facade.list_generations.return_value = GenerationListTransfer(items=[])

    client.get("/api/generations?limit=10")

    business_dto = mock_facade.list_generations.await_args.args[0]
    assert business_dto.limit == 10


# ─── GET /api/generations/{id} ───────────────────────────────────────────────
def test_get_generation_returns_200(client, mock_facade, sample_generation):
    mock_facade.get_generation.return_value = sample_generation

    r = client.get("/api/generations/42")

    assert r.status_code == 200
    assert r.json()["id"] == 42


def test_get_generation_returns_404_when_missing(client, mock_facade):
    mock_facade.get_generation.return_value = None

    r = client.get("/api/generations/999")

    assert r.status_code == 404


def test_get_generation_passes_id_to_facade(client, mock_facade, sample_generation):
    mock_facade.get_generation.return_value = sample_generation

    client.get("/api/generations/42")

    business_dto = mock_facade.get_generation.await_args.args[0]
    assert business_dto.id == 42


# ─── GET /api/generations/{id}/stream ────────────────────────────────────────
def test_stream_generation_returns_sse(client, mock_facade):
    events = [
        LlmEventTransfer(type=LlmEventType.TOOL_START, tool="set_html"),
        LlmEventTransfer(type=LlmEventType.TOOL_COMPLETE, tool="set_html"),
        LlmEventTransfer(
            type=LlmEventType.DONE,
            result=LandingResultTransfer(html="<h1>x</h1>", css="", js=""),
        ),
    ]

    async def fake_stream(dto):
        for e in events:
            yield e

    mock_facade.stream_generation = fake_stream

    with client.stream("GET", "/api/generations/42/stream") as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        body = b"".join(r.iter_bytes()).decode()

    # Каждое событие — отдельный SSE-message с своим event-name
    assert "event: tool_start" in body
    assert "event: tool_complete" in body
    assert "event: done" in body


def test_stream_generation_emits_event_data_json(client, mock_facade):
    events = [LlmEventTransfer(type=LlmEventType.TOOL_START, tool="set_html")]

    async def fake_stream(dto):
        for e in events:
            yield e

    mock_facade.stream_generation = fake_stream

    with client.stream("GET", "/api/generations/42/stream") as r:
        body = b"".join(r.iter_bytes()).decode()

    # Парсим data-строку как JSON и проверяем поля
    data_line = next(line for line in body.splitlines() if line.startswith("data: "))
    payload = json.loads(data_line.removeprefix("data: "))
    assert payload["type"] == "tool_start"
    assert payload["tool"] == "set_html"
