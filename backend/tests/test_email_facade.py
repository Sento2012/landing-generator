"""Тесты публичных методов EmailFacade."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.email.domain.dto.email_message import EmailMessageTransfer
from app.email.domain.facade import EmailFacade
from app.email.domain.factory import EmailFactory


@pytest.fixture
def mock_scheduler():
    return MagicMock()


@pytest.fixture
def mock_sender():
    return AsyncMock()


@pytest.fixture
def mock_factory(mock_scheduler, mock_sender):
    factory = MagicMock(spec=EmailFactory)
    factory.create_scheduler.return_value = mock_scheduler
    factory.create_sender.return_value = mock_sender
    return factory


@pytest.fixture
def facade(mock_factory):
    return EmailFacade(mock_factory)


@pytest.fixture
def sample_message():
    return EmailMessageTransfer(
        to="user@test.com",
        subject="Hello",
        body="World",
    )


def test_schedule_email_delegates_to_scheduler(facade, mock_scheduler, sample_message):
    facade.schedule_email(sample_message)
    mock_scheduler.schedule.assert_called_once_with(sample_message)


async def test_send_email_delegates_to_sender(facade, mock_sender, sample_message):
    await facade.send_email(sample_message)
    mock_sender.send.assert_awaited_once_with(sample_message)
