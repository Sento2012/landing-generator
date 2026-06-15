"""Итоговый результат генерации лендинга — три плоские строки."""
from pydantic import BaseModel


class LandingResultTransfer(BaseModel):
    html: str = ""
    css: str = ""
    js: str = ""
