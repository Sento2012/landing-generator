"""Публичная дверь Email-модуля."""
from app.email.domain.dto.email_message import EmailMessageTransfer
from app.email.domain.factory import EmailFactory


class EmailFacade:
    def __init__(self, factory: EmailFactory) -> None:
        self._factory = factory

    def schedule_email(self, message: EmailMessageTransfer) -> None:
        """Поставить email в очередь — отправка произойдёт в email worker'е."""
        self._factory.create_scheduler().schedule(message)

    async def send_email(self, message: EmailMessageTransfer) -> None:
        """Отправить email синхронно через SMTP. Вызывается из email worker'а."""
        await self._factory.create_sender().send(message)
