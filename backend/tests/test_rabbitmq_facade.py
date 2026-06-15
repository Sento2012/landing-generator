"""Тесты публичных методов RabbitmqFacade.

Facade берёт TaskPublisher из Factory и зовёт publish(). Тестируем что:
- Создаётся publisher через factory.
- В publisher передаётся ровно тот TaskMessage что пришёл в Facade.
"""
from unittest.mock import MagicMock

import pytest

from app.rabbitmq.domain.dto.task_message import TaskMessage
from app.rabbitmq.domain.facade import RabbitmqFacade
from app.rabbitmq.domain.factory import RabbitmqFactory


@pytest.fixture
def mock_publisher():
    return MagicMock()


@pytest.fixture
def mock_factory(mock_publisher):
    factory = MagicMock(spec=RabbitmqFactory)
    factory.create_task_publisher.return_value = mock_publisher
    return factory


@pytest.fixture
def facade(mock_factory):
    return RabbitmqFacade(mock_factory)


def test_publish_task_delegates_to_publisher(facade, mock_factory, mock_publisher):
    message = TaskMessage(task_name="some.task", args=[1, "x"], kwargs={"k": "v"})

    facade.publish_task(message)

    mock_factory.create_task_publisher.assert_called_once()
    mock_publisher.publish.assert_called_once_with(message)


def test_publish_task_with_default_args(facade, mock_publisher):
    message = TaskMessage(task_name="another.task")

    facade.publish_task(message)

    published = mock_publisher.publish.call_args.args[0]
    assert published.task_name == "another.task"
    assert published.args == []
    assert published.kwargs == {}
