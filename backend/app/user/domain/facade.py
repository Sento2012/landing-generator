"""Публичная дверь User-модуля."""
from app.user.domain.dto.jwt_token import JwtPayloadTransfer, JwtTokenTransfer
from app.user.domain.dto.user import UserTransfer
from app.user.domain.dto.user_create import UserCreateTransfer
from app.user.domain.dto.user_credentials import UserCredentialsTransfer
from app.user.domain.factory import UserFactory


class UserFacade:
    def __init__(self, factory: UserFactory) -> None:
        self._factory = factory

    async def register(self, dto: UserCreateTransfer) -> UserTransfer:
        return await self._factory.create_registration_service().register(dto)

    async def authenticate(
        self,
        credentials: UserCredentialsTransfer,
    ) -> JwtTokenTransfer:
        return await self._factory.create_authentication_service().authenticate(
            credentials
        )

    def decode_token(self, token: str) -> JwtPayloadTransfer:
        return self._factory.create_jwt_service().decode(token)

    async def get_user_by_id(self, user_id: int) -> UserTransfer | None:
        return await self._factory.create_repository().find_by_id(user_id)
