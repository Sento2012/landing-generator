"""Repository — операции ЧТЕНИЯ юзеров."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.user.domain.dto.user import UserTransfer
from app.user.domain.models.entity import UserEntity


class UserRepository:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def find_by_id(self, user_id: int) -> UserTransfer | None:
        async with self._session_factory() as session:
            entity = await session.get(UserEntity, user_id)
            return UserTransfer.model_validate(entity) if entity else None

    async def find_by_email(self, email: str) -> UserTransfer | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserEntity).where(UserEntity.email == email)
            )
            entity = result.scalar_one_or_none()
            return UserTransfer.model_validate(entity) if entity else None

    async def find_entity_by_email(self, email: str) -> UserEntity | None:
        """Возвращает ORM-сущность с password_hash. Используется только для
        проверки пароля в AuthenticationService — наружу UserTransfer не отдаёт.
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserEntity).where(UserEntity.email == email)
            )
            return result.scalar_one_or_none()
