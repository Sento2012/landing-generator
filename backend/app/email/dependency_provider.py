"""Wiring модуля Email."""
from app.email.domain.facade import EmailFacade
from app.email.domain.factory import EmailFactory
from app.rabbitmq.domain.facade import RabbitmqFacade


def build_email_facade(
    rabbitmq_facade: RabbitmqFacade,
    smtp_host: str,
    smtp_port: int,
    smtp_from: str,
) -> EmailFacade:
    factory = EmailFactory(
        rabbitmq_facade=rabbitmq_facade,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_from=smtp_from,
    )
    return EmailFacade(factory)
