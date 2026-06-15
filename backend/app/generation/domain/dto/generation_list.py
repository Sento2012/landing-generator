"""Envelope-Transfer для list-метода. Список + место под total/has_more/cursor в будущем."""
from pydantic import BaseModel

from app.generation.domain.dto.generation import GenerationListItemTransfer


class GenerationListTransfer(BaseModel):
    items: list[GenerationListItemTransfer]
