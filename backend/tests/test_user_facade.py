"""Тесты публичных методов UserFacade."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.user.domain.dto.jwt_token import JwtPayloadTransfer, JwtTokenTransfer
from app.user.domain.dto.user import UserTransfer
from app.user.domain.dto.user_create import UserCreateTransfer
from app.user.domain.dto.user_credentials import UserCredentialsTransfer
from app.user.domain.facade import UserFacade
from app.user.domain.factory import UserFactory


@pytest.fixture
def mock_registration_service():
    return AsyncMock()


@pytest.fixture
def mock_auth_service():
    return AsyncMock()


@pytest.fixture
def mock_jwt_service():
    return MagicMock()


@pytest.fixture
def mock_repository():
    return AsyncMock()


@pytest.fixture
def mock_factory(
    mock_registration_service,
    mock_auth_service,
    mock_jwt_service,
    mock_repository,
):
    factory = MagicMock(spec=UserFactory)
    factory.create_registration_service.return_value = mock_registration_service
    factory.create_authentication_service.return_value = mock_auth_service
    factory.create_jwt_service.return_value = mock_jwt_service
    factory.create_repository.return_value = mock_repository
    return factory


@pytest.fixture
def facade(mock_factory):
    return UserFacade(mock_factory)


@pytest.fixture
def sample_user():
    return UserTransfer(
        id=42,
        email="user@test.com",
        created_at=datetime(2026, 6, 16, 12, 0, 0),
    )


# ─── register ────────────────────────────────────────────────────────────────
async def test_register_delegates_to_registration_service(
    facade, mock_registration_service, sample_user,
):
    dto = UserCreateTransfer(email="user@test.com", password="strongpass123")
    mock_registration_service.register.return_value = sample_user

    result = await facade.register(dto)

    mock_registration_service.register.assert_awaited_once_with(dto)
    assert result is sample_user


# ─── authenticate ────────────────────────────────────────────────────────────
async def test_authenticate_delegates_to_auth_service(facade, mock_auth_service):
    creds = UserCredentialsTransfer(email="user@test.com", password="pass")
    token = JwtTokenTransfer(access_token="abc.def.ghi", token_type="bearer", expires_in=1800)
    mock_auth_service.authenticate.return_value = token

    result = await facade.authenticate(creds)

    mock_auth_service.authenticate.assert_awaited_once_with(creds)
    assert result is token


# ─── decode_token ────────────────────────────────────────────────────────────
def test_decode_token_delegates_to_jwt_service(facade, mock_jwt_service):
    payload = JwtPayloadTransfer(user_id=42, email="user@test.com")
    mock_jwt_service.decode.return_value = payload

    result = facade.decode_token("abc.def.ghi")

    mock_jwt_service.decode.assert_called_once_with("abc.def.ghi")
    assert result is payload


# ─── get_user_by_id ──────────────────────────────────────────────────────────
async def test_get_user_by_id_returns_user(facade, mock_repository, sample_user):
    mock_repository.find_by_id.return_value = sample_user

    result = await facade.get_user_by_id(42)

    mock_repository.find_by_id.assert_awaited_once_with(42)
    assert result is sample_user


async def test_get_user_by_id_returns_none_when_missing(facade, mock_repository):
    mock_repository.find_by_id.return_value = None

    result = await facade.get_user_by_id(999)

    assert result is None
