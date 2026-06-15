"""Идентификатор генерации для get/stream."""
from pydantic import BaseModel


class GenerationByIdTransfer(BaseModel):
    id: int
