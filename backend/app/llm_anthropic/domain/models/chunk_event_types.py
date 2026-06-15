"""Типы событий Anthropic streaming-протокола.

Внутренние Anthropic-константы. Стандартный API messages.stream() шлёт чанки
с разными `type`. Эти enum'ы — внутренние сравнения, наружу не уходят.
"""
from enum import StrEnum


class AnthropicChunkType(StrEnum):
    CONTENT_BLOCK_START = "content_block_start"
    CONTENT_BLOCK_DELTA = "content_block_delta"
    CONTENT_BLOCK_STOP = "content_block_stop"


class AnthropicBlockType(StrEnum):
    """Тип content-block'а внутри content_block_start."""
    TOOL_USE = "tool_use"
    TEXT = "text"


class AnthropicDeltaType(StrEnum):
    """Тип delta внутри content_block_delta."""
    INPUT_JSON_DELTA = "input_json_delta"
    TEXT_DELTA = "text_delta"
