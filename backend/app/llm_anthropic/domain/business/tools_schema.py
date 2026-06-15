"""Сборка tools-схемы под Anthropic-формат.

Знает их формат: {name, description, input_schema} без обёртки function (в отличие от OpenAI).
Конкретные описания tools'ов приходят параметром — модуль не зависит от
содержимого `llm/domain/prompt.py`.
"""
from app.llm.domain.models.tool_name import LlmToolName


def build_anthropic_tools_schema(
    tool_descriptions: dict[LlmToolName, dict[str, str]],
) -> list[dict]:
    """Общие описания → Anthropic-формат."""
    return [
        {
            "name": str(name),
            "description": meta["description"],
            "input_schema": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": meta["content_description"],
                    },
                },
                "required": ["content"],
            },
        }
        for name, meta in tool_descriptions.items()
    ]
