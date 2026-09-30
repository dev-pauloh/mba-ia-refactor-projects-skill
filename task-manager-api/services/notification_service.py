import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class NotificationService:
    """Envia notificações por e-mail. Sem SMTP_HOST configurado, apenas registra em log."""

    def __init__(self, host, port, user, password, timeout=10):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout

    def send_email(self, to, subject, body):
        if not self.host:
            logger.info('SMTP não configurado; notificação para %s não enviada: %s', to, subject)
            return False

        message = EmailMessage()
        message['From'] = self.user
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as server:
                server.starttls()
                if self.user:
                    server.login(self.user, self.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            logger.exception('Falha ao enviar e-mail para %s', to)
            return False
        logger.info('E-mail enviado para %s', to)
        return True

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        return self.send_email(user.email, subject, body)
