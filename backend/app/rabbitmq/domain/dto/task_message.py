from typing import Any

from pydantic import BaseModel, Field


class TaskMessage(BaseModel):
    task_name: str = Field(min_length=1)
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)
    # Имя очереди в брокере. None → дефолтная очередь Celery ("celery").
    queue: str | None = None
