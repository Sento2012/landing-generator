"""EmailScheduler — публикует задачу отправки email в очередь."""
from app.email.domain.business.task_names import EMAIL_QUEUE, EMAIL_SEND
from app.email.domain.dto.email_message import EmailMessageTransfer
from app.rabbitmq.domain.dto.task_message import TaskMessage
from app.rabbitmq.domain.facade import RabbitmqFacade


class EmailScheduler:
    def __init__(self, rabbitmq_facade: RabbitmqFacade) -> None:
        self._rabbitmq = rabbitmq_facade

    def schedule(self, message: EmailMessageTransfer) -> None:
        self._rabbitmq.publish_task(
            TaskMessage(
                task_name=EMAIL_SEND,
                args=[message.model_dump()],
                queue=EMAIL_QUEUE,
            )
        )
