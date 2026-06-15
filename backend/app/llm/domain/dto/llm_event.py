"""Унифицированное событие от любого LLM-провайдера.

Этот тип — единственное, что наружу видит мир. Какой именно провайдер
эти события сгенерировал — внешний код не знает.
"""
from enum import StrEnum

from pydantic import BaseModel

from app.llm.domain.dto.landing_result import LandingResultTransfer


class LlmEventType(StrEnum):
    TOOL_START = "tool_start"
    TOOL_DELTA = "tool_delta"
    TOOL_COMPLETE = "tool_complete"
    DONE = "done"
    ERROR = "error"


class LlmEventTransfer(BaseModel):
    type: LlmEventType
    tool: str | None = None
    partial: str | None = None
    result: LandingResultTransfer | None = None
    message: str | None = None
