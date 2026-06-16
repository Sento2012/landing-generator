"""Тесты HTTP endpoints (Generation controller + /health).

Facade и CurrentUser подменяются через app.dependency_overrides — реальный
LLM/БД/auth не дёргаются. TestClient создаётся БЕЗ `with` — lifespan не запускается.
"""
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
from app.main import app
from app.shared.dependency_provider import get_generation_facade
from app.user.client.auth_dependency import get_current_user
from app.user.domain.dto.user import UserTransfer


@pytest.fixture
def fake_user():
    return UserTransfer(
        id=1,
        email="test@example.com",
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def mock_facade():
    facade = MagicMock()
    facade.create_generation = AsyncMock()
    facade.get_generation = AsyncMock()
    facade.list_generations = AsyncMock()
    return facade


@pytest.fixture
def client(mock_facade, fake_user):
    app.dependency_overrides[get_generation_facade] = lambda: mock_facade
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_generation():
    return GenerationTransfer(
        id=42,
        user_id=1,
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
    assert body["user_id"] == 1
    assert body["status"] == "completed"


def test_create_generation_passes_user_id_from_current_user(
    client, mock_facade, sample_generation,
):
    mock_facade.create_generation.return_value = sample_generation

    client.post("/api/generations", json={"prompt": "test", "provider": "anthropic"})

    business_dto = mock_facade.create_generation.await_args.args[0]
    assert isinstance(business_dto, GenerationCreateTransfer)
    assert business_dto.user_id == 1
    assert business_dto.prompt == "test"
    assert str(business_dto.provider) == "anthropic"


def test_create_generation_rejects_short_prompt(client):
    r = client.post("/api/generations", json={"prompt": "hi"})
    assert r.status_code == 422


def test_create_generation_rejects_unknown_provider(client):
    r = client.post("/api/generations", json={"prompt": "test", "provider": "gpt-4"})
    assert r.status_code == 422


# ─── GET /api/generations ────────────────────────────────────────────────────
def test_list_generations_returns_envelope(client, mock_facade):
    mock_facade.list_generations.return_value = GenerationListTransfer(
        items=[
            GenerationListItemTransfer(
                id=1, user_id=1, prompt="p1", status="completed", provider="openai",
                created_at=datetime(2026, 1, 1),
            ),
        ]
    )

    r = client.get("/api/generations")

    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert body["items"][0]["id"] == 1
    assert body["items"][0]["user_id"] == 1


def test_list_generations_filters_by_current_user(client, mock_facade):
    mock_facade.list_generations.return_value = GenerationListTransfer(items=[])

    client.get("/api/generations?limit=10")

    business_dto = mock_facade.list_generations.await_args.args[0]
    assert business_dto.user_id == 1
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


def test_get_generation_passes_user_id_for_ownership_check(
    client, mock_facade, sample_generation,
):
    mock_facade.get_generation.return_value = sample_generation

    client.get("/api/generations/42")

    business_dto = mock_facade.get_generation.await_args.args[0]
    assert business_dto.id == 42
    assert business_dto.user_id == 1
