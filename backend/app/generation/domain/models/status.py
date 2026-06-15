"""Статусы жизненного цикла генерации.

StrEnum (Python 3.11+) совместим со String-колонкой в БД — значения уходят
в постгрес как обычные строки. Никаких миграций.

Lifecycle:
    pending  →  running  →  completed
                       \\→  failed
"""
from enum import StrEnum


class GenerationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
