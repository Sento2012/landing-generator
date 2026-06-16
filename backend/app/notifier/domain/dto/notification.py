"""Что отправляем по RabbitMQ.

routing_key — куда роутится сообщение в topic exchange.
payload — JSON-сериализуемое тело (в WS уйдёт как есть).
"""
from typing import Any

from pydantic import BaseModel, Field


class NotificationTransfer(BaseModel):
    routing_key: str = Field(min_length=1)
    payload: dict[str, Any]
