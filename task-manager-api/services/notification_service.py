import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class NotificationService:
    """Envia notificações por e-mail; configuração e transporte SMTP são injetados."""

    def __init__(self, host, port, user, password, smtp_factory=smtplib.SMTP):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.smtp_factory = smtp_factory

    def send_email(self, to, subject, body):
        if not self.host:
            logger.warning('SMTP não configurado; e-mail para %s não enviado', to)
            return False

        message = EmailMessage()
        message['From'] = self.user
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)

        try:
            with self.smtp_factory(self.host, self.port) as server:
                server.starttls()
                if self.user:
                    server.login(self.user, self.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            logger.exception('Erro ao enviar e-mail para %s', to)
            return False

        logger.info('E-mail enviado para %s', to)
        return True

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
                f"Prioridade: {task.priority}\nStatus: {task.status}")
        return self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        return self.send_email(user.email, subject, body)
