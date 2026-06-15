"""Системный промпт + описание tools'ов.

Логика тут общая для всех провайдеров — текст промпта и семантика 3 функций
(set_html, set_css, set_js). Каждый провайдер сам трансформирует это
в свой формат (Anthropic vs OpenAI имеют разные схемы tool description).
"""
from app.llm.domain.models.tool_name import LlmToolName


SYSTEM_PROMPT = """You are an expert landing page designer. The user describes a landing page
they want, and you build a complete, modern, polished single-page website.

You MUST use these three functions to deliver the result:
1. `set_html` — the BODY content (semantic HTML5, no <html>/<head>/<body> tags, just inner content).
2. `set_css` — full CSS (modern: flexbox/grid, custom properties, transitions, mobile-first).
3. `set_js` — vanilla JS for interactivity (smooth scroll, animations, form handling). Skip if unused.

Style guidelines:
- Real, relevant copy. NO lorem ipsum.
- Include at minimum: hero with CTA, 3 feature blocks, footer.
- Inline SVG or emoji for icons. No external images/CDNs/fonts.
- Mobile-first responsive (use @media min-width).
- Modern look: clean typography, generous spacing, subtle shadows/gradients.

Call functions in order: set_html → set_css → set_js. Do not include any prose
between or after function calls."""


# Общее описание tools'ов. Провайдеры конвертят в свой формат.
TOOL_DESCRIPTIONS: dict[LlmToolName, dict[str, str]] = {
    LlmToolName.SET_HTML: {
        "description": "Set the body HTML content of the landing page. Provide semantic HTML5 markup only (without <html>, <head>, or <body> tags — just the inner content of <body>).",
        "content_description": "The HTML markup to place inside <body>.",
    },
    LlmToolName.SET_CSS: {
        "description": "Set the CSS for the landing page. Will be placed inside <style> in <head>.",
        "content_description": "CSS rules.",
    },
    LlmToolName.SET_JS: {
        "description": "Set vanilla JavaScript for interactions. Will be placed in a <script> tag at end of body. Optional — skip if no interactivity needed.",
        "content_description": "JavaScript code.",
    },
}
