"""RegistrationService — оркестратор регистрации юзера.

Сценарий:
1. Проверить что email не занят.
2. Захэшировать пароль.
3. Сохранить юзера.
4. Отправить welcome-email (через очередь — фактическая отправка в email worker).
"""
from app.email.domain.dto.email_message import EmailMessageTransfer
from app.email.domain.facade import EmailFacade
from app.user.domain.business.password_hasher import PasswordHasher
from app.user.domain.dto.user import UserTransfer
from app.user.domain.dto.user_create import UserCreateTransfer
from app.user.domain.persistence.entity_manager import UserEntityManager
from app.user.domain.persistence.repository import UserRepository


class EmailAlreadyTakenError(Exception):
    """Email уже зарегистрирован в системе."""


class RegistrationService:
    def __init__(
        self,
        repository: UserRepository,
        entity_manager: UserEntityManager,
        password_hasher: PasswordHasher,
        email_facade: EmailFacade,
    ) -> None:
        self._repo = repository
        self._em = entity_manager
        self._hasher = password_hasher
        self._email = email_facade

    async def register(self, dto: UserCreateTransfer) -> UserTransfer:
        if await self._repo.find_by_email(dto.email) is not None:
            raise EmailAlreadyTakenError(dto.email)

        user = await self._em.create(
            email=dto.email,
            password_hash=self._hasher.hash(dto.password),
        )

        self._email.schedule_email(EmailMessageTransfer(
            to=user.email,
            subject="Welcome to Landing Generator",
            body=(
                f"Hi!\n\n"
                f"Your account ({user.email}) is ready. Start generating landings "
                f"at http://localhost:5173.\n\n"
                f"— The Landing Generator team"
            ),
        ))

        return user
