"""Сборка tools-схемы под OpenAI-формат.

Знает их формат: {"type": "function", "function": {name, description, parameters}}.
Конкретные описания tools'ов приходят параметром — модуль не зависит от
содержимого `llm/domain/prompt.py`.
"""
from app.llm.domain.models.tool_name import LlmToolName


def build_openai_tools_schema(
    tool_descriptions: dict[LlmToolName, dict[str, str]],
) -> list[dict]:
    """Общие описания → OpenAI-формат."""
    return [
        {
            "type": "function",
            "function": {
                "name": str(name),
                "description": meta["description"],
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": meta["content_description"],
                        },
                    },
                    "required": ["content"],
                    "additionalProperties": False,
                },
            },
        }
        for name, meta in tool_descriptions.items()
    ]
