"""Factory модуля User — создаёт сервисы аутентификации/регистрации."""
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.email.domain.facade import EmailFacade
from app.user.domain.business.authentication_service import AuthenticationService
from app.user.domain.business.jwt_service import JwtService
from app.user.domain.business.password_hasher import PasswordHasher
from app.user.domain.business.registration_service import RegistrationService
from app.user.domain.persistence.entity_manager import UserEntityManager
from app.user.domain.persistence.repository import UserRepository


class UserFactory:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        email_facade: EmailFacade,
        jwt_secret: str,
        jwt_expires_minutes: int,
    ) -> None:
        self._session_factory = session_factory
        self._email_facade = email_facade
        self._jwt_secret = jwt_secret
        self._jwt_expires_minutes = jwt_expires_minutes

    def create_repository(self) -> UserRepository:
        return UserRepository(self._session_factory)

    def create_entity_manager(self) -> UserEntityManager:
        return UserEntityManager(self._session_factory)

    def create_password_hasher(self) -> PasswordHasher:
        return PasswordHasher()

    def create_jwt_service(self) -> JwtService:
        return JwtService(
            secret=self._jwt_secret,
            expires_minutes=self._jwt_expires_minutes,
        )

    def create_registration_service(self) -> RegistrationService:
        return RegistrationService(
            repository=self.create_repository(),
            entity_manager=self.create_entity_manager(),
            password_hasher=self.create_password_hasher(),
            email_facade=self._email_facade,
        )

    def create_authentication_service(self) -> AuthenticationService:
        return AuthenticationService(
            repository=self.create_repository(),
            password_hasher=self.create_password_hasher(),
            jwt_service=self.create_jwt_service(),
        )
