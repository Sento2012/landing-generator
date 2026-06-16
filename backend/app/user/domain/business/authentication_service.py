"""AuthenticationService — оркестратор логина: проверка пароля + выдача JWT."""
from app.user.domain.business.jwt_service import JwtService
from app.user.domain.business.password_hasher import PasswordHasher
from app.user.domain.dto.jwt_token import JwtTokenTransfer
from app.user.domain.dto.user import UserTransfer
from app.user.domain.dto.user_credentials import UserCredentialsTransfer
from app.user.domain.persistence.repository import UserRepository


class InvalidCredentialsError(Exception):
    """Email/пароль не совпадает с записью в БД."""


class AuthenticationService:
    def __init__(
        self,
        repository: UserRepository,
        password_hasher: PasswordHasher,
        jwt_service: JwtService,
    ) -> None:
        self._repo = repository
        self._hasher = password_hasher
        self._jwt = jwt_service

    async def authenticate(
        self,
        credentials: UserCredentialsTransfer,
    ) -> JwtTokenTransfer:
        entity = await self._repo.find_entity_by_email(credentials.email)
        if entity is None or not self._hasher.verify(
            credentials.password, entity.password_hash,
        ):
            raise InvalidCredentialsError()
        user = UserTransfer.model_validate(entity)
        return self._jwt.issue(user)
