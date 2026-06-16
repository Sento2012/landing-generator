"""Имена exchange'ей RabbitMQ.

Один topic exchange для всех уведомлений; роутинг идёт через routing_key.
"""
from enum import StrEnum


class ExchangeName(StrEnum):
    NOTIFICATIONS = "notifications"
