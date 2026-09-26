import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

import structlog

from app.common.decoys import email_digest
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

    def send_verification_email(self, to_email: str, token: str, frontend_url: str) -> None:
        # Sent to an address nobody has verified yet: no requester-chosen text, not
        # even escaped — a registrant picks the display name and the recipient (#1856).
        url = f"{frontend_url}/verify-email/{token}"
        html = f"""
        <h2>Email Verification</h2>
        <p>Hello,</p>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{escape(url)}">Verify Email</a></p>
        <p>This link expires in 24 hours.</p>
        """
        self._send(to_email, "Kamerplanter — Email Verification", html)

    def send_password_reset_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None:
        url = f"{frontend_url}/password-reset/{token}"
        html = f"""
        <h2>Password Reset</h2>
        <p>Hello {escape(display_name)},</p>
        <p>Click the link below to reset your password:</p>
        <p><a href="{escape(url)}">Reset Password</a></p>
        <p>This link expires in 1 hour. If you did not request this, ignore this email.</p>
        """
        self._send(to_email, "Kamerplanter — Password Reset", html)

    def send_email_change_email(self, to_email: str, token: str, frontend_url: str) -> None:
        # To the requested new address (#1848): not verified, so no requester-chosen
        # text (#1856). The link opens the page that confirms the change.
        url = f"{frontend_url}/email-change/{token}"
        html = f"""
        <h2>Confirm your new email address</h2>
        <p>Hello,</p>
        <p>A Kamerplanter account asked to use this address from now on. To confirm, open the link below:</p>
        <p><a href="{escape(url)}">Confirm the new email address</a></p>
        <p>The link expires in 24 hours. If you did not expect this mail, ignore it — nothing changes.</p>
        """
        self._send(to_email, "Kamerplanter — Confirm your new email address", html)

    def send_step_up_code_email(self, to_email: str, display_name: str, code: str, purpose: str) -> None:
        html = f"""
        <h2>Confirmation code</h2>
        <p>Hello {escape(display_name)},</p>
        <p>Use this code to confirm that you want to <strong>{escape(purpose)}</strong>.
        It confirms this action only.</p>
        <p style="font-size: 1.5em; letter-spacing: 0.2em;"><strong>{escape(code)}</strong></p>
        <p>The code is valid for 10 minutes and can be used once.</p>
        <p>If you did not request this code, someone may be signed in to your account:
        sign out all sessions in your account settings and reset your password.</p>
        """
        self._send(to_email, "Kamerplanter — Confirmation code", html)

    def send_notification_email(self, to_email: str, subject: str, html_body: str) -> None:
        self._send(to_email, subject, html_body)
