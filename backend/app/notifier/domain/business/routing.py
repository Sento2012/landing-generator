"""Конвенция routing-ключей для notifications-exchange.

Формат: `user.{user_id}.{topic}` — где topic классифицирует событие
(gen, system, ...). WS-подписка использует паттерн `user.{user_id}.*` —
получает всё про конкретного пользователя.
"""
from enum import StrEnum


class NotificationTopic(StrEnum):
    GENERATION = "gen"


def routing_key_for_user(user_id: int, topic: NotificationTopic) -> str:
    return f"user.{user_id}.{topic}"


def routing_pattern_for_user(user_id: int) -> str:
    return f"user.{user_id}.*"
