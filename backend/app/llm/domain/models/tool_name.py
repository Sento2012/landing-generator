"""Имена tools'ов, которые LLM должна вызвать для сборки лендинга.

Один источник правды — используется и в prompt.py (descriptions),
и в провайдерах (для роутинга tool call'ов в html/css/js).
"""
from enum import StrEnum


class LlmToolName(StrEnum):
    SET_HTML = "set_html"
    SET_CSS = "set_css"
    SET_JS = "set_js"
