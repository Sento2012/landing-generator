"""Вход на execute_generation — вызывается из Celery worker (системный контекст,
без ownership-проверки, поэтому user_id не нужен)."""
from pydantic import BaseModel


class GenerationExecuteTransfer(BaseModel):
    id: int
