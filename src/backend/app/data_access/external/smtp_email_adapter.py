import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog

from app.common.decoys import email_digest
from app.data_access.external.templated_email_adapter import TemplatedEmailAdapter

logger = structlog.get_logger()


class SmtpEmailAdapter(TemplatedEmailAdapter):
    """Production email adapter using SMTP; the mail texts come from :class:`TemplatedEmailAdapter`."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._use_tls = use_tls

    def _send(self, to_email: str, subject: str, html_body: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._from_email
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self._host, self._port) as server:
                if self._use_tls:
                    server.starttls()
                if self._username:
                    server.login(self._username, self._password)
                server.sendmail(self._from_email, to_email, msg.as_string())
            logger.info("email_sent", to_sha256=email_digest(to_email), subject=subject)
        except Exception as exc:
            # A digest, never the address, and the exception type without its
            # text or traceback: ``SMTPRecipientsRefused`` names the refused
            # address, and a log stream has no retention rule (#1773 review
            # GDPR-004). The caller receives the exception unchanged.
            logger.error(
                "email_send_failed",
                to_sha256=email_digest(to_email),
                subject=subject,
                error_type=type(exc).__name__,
            )
            raise
