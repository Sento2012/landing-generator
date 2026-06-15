"""Имена Celery-задач Generation-домена.

Отдельный файл без импортов celery — чтобы и producer (facade), и task definition
могли импортить, не таща celery_app по цепочке.
"""

GENERATION_RUN = "generation.run"
