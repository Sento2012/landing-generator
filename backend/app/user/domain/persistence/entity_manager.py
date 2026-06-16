"""EntityManager — операции ЗАПИСИ юзеров."""
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.user.domain.dto.user import UserTransfer
from app.user.domain.models.entity import UserEntity


class UserEntityManager:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def create(self, email: str, password_hash: str) -> UserTransfer:
        async with self._session_factory() as session:
            entity = UserEntity(email=email, password_hash=password_hash)
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return UserTransfer.model_validate(entity)
