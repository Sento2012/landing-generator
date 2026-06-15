"""Сообщение для отправки task'и в очередь."""
from typing import Any

from pydantic import BaseModel, Field


class TaskMessage(BaseModel):
    """Что отправляем в брокер: имя зарегистрированной task'и и её аргументы."""

    task_name: str = Field(min_length=1)
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)
