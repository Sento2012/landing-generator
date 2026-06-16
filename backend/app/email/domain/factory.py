"""Factory модуля Email — создаёт Scheduler (producer) и Sender (worker-side)."""
from app.email.domain.business.email_scheduler import EmailScheduler
from app.email.domain.business.email_sender import EmailSender
from app.rabbitmq.domain.facade import RabbitmqFacade


class EmailFactory:
    def __init__(
        self,
        rabbitmq_facade: RabbitmqFacade,
        smtp_host: str,
        smtp_port: int,
        smtp_from: str,
    ) -> None:
        self._rabbitmq_facade = rabbitmq_facade
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._smtp_from = smtp_from

    def create_scheduler(self) -> EmailScheduler:
        return EmailScheduler(rabbitmq_facade=self._rabbitmq_facade)

    def create_sender(self) -> EmailSender:
        return EmailSender(
            host=self._smtp_host,
            port=self._smtp_port,
            from_address=self._smtp_from,
        )
