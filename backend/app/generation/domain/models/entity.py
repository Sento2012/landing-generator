"""ORM-сущность Generation. Единственный файл, импортирующий SQLAlchemy в этом модуле."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.generation.domain.models.status import GenerationStatus
from app.shared.database import Base


class GenerationEntity(Base):
    __tablename__ = "generations"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Владелец — для multi-tenancy и ownership-проверок в HTTP-слое.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    # Хранится как строка в БД, но в Python — GenerationStatus (StrEnum)
    status: Mapped[str] = mapped_column(String(20), default=GenerationStatus.PENDING)
    # Какой LLM-провайдер генерирует — часть identity (replay должен быть тем же)
    provider: Mapped[str] = mapped_column(String(20))

    html: Mapped[str | None] = mapped_column(Text, nullable=True)
    css: Mapped[str | None] = mapped_column(Text, nullable=True)
    js: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
