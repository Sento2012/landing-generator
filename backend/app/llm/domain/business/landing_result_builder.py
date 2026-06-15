"""Помощник для маппинга tool-call'ов в LandingResultTransfer.

Логика «какое имя tool'а в какое поле результата идёт» одинаковая
для всех провайдеров — здесь общая точка.
"""
from app.llm.domain.dto.landing_result import LandingResultTransfer
from app.llm.domain.models.tool_name import LlmToolName


def apply_tool_content(
    result: LandingResultTransfer,
    tool_name: str,
    content: str,
) -> None:
    """Положить content в соответствующее поле result по имени tool'а.

    Mutates result in-place. Неизвестные tool_name молча игнорируются —
    провайдер мог вернуть что-то лишнее, наш result стерпит.
    """
    if tool_name == LlmToolName.SET_HTML:
        result.html = content
    elif tool_name == LlmToolName.SET_CSS:
        result.css = content
    elif tool_name == LlmToolName.SET_JS:
        result.js = content
