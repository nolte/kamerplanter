import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog

from app.domain.interfaces.email_service import IEmailService

logger = structlog.get_logger()


class SmtpEmailAdapter(IEmailService):
    """Production email adapter using SMTP."""

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
            logger.info("email_sent", to=to_email, subject=subject)
        except Exception:
            logger.error("email_send_failed", to=to_email, subject=subject, exc_info=True)
            raise

    def send_verification_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None:
        url = f"{frontend_url}/verify-email/{token}"
        html = f"""
        <h2>Email Verification</h2>
        <p>Hello {display_name},</p>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{url}">Verify Email</a></p>
        <p>This link expires in 24 hours.</p>
        """
        self._send(to_email, "Kamerplanter — Email Verification", html)

    def send_password_reset_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None:
        url = f"{frontend_url}/password-reset/{token}"
        html = f"""
        <h2>Password Reset</h2>
        <p>Hello {display_name},</p>
        <p>Click the link below to reset your password:</p>
        <p><a href="{url}">Reset Password</a></p>
        <p>This link expires in 1 hour. If you did not request this, ignore this email.</p>
        """
        self._send(to_email, "Kamerplanter — Password Reset", html)
