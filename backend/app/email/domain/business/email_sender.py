"""EmailSender — фактически шлёт email через SMTP. Вызывается из Celery worker."""
import aiosmtplib
from email.message import EmailMessage as RawEmailMessage

from app.email.domain.dto.email_message import EmailMessageTransfer


class EmailSender:
    def __init__(self, host: str, port: int, from_address: str) -> None:
        self._host = host
        self._port = port
        self._from = from_address

    async def send(self, message: EmailMessageTransfer) -> None:
        raw = RawEmailMessage()
        raw["From"] = self._from
        raw["To"] = message.to
        raw["Subject"] = message.subject
        raw.set_content(message.body)

        # Mailhog без TLS/auth. В проде — start_tls=True + auth.
        await aiosmtplib.send(
            raw,
            hostname=self._host,
            port=self._port,
        )
