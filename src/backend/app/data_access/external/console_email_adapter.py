import structlog

from app.common.decoys import email_digest
from app.domain.interfaces.email_service import IEmailService

logger = structlog.get_logger()


class ConsoleEmailAdapter(IEmailService):
    """Development email adapter that logs emails to console.

    The recipient is logged as a digest (``to_sha256``), never the address
    (#1773 review GDPR-004): a log stream has no retention rule of its own.
    """

    def send_verification_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None:
        url = f"{frontend_url}/verify-email/{token}"
        logger.info(
            "email_verification",
            to_sha256=email_digest(to_email),
            name=display_name,
            verification_url=url,
        )

    def send_password_reset_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None:
        url = f"{frontend_url}/password-reset/{token}"
        logger.info(
            "email_password_reset",
            to_sha256=email_digest(to_email),
            name=display_name,
            reset_url=url,
        )

    def send_notification_email(self, to_email: str, subject: str, html_body: str) -> None:
        logger.info(
            "email_notification",
            to_sha256=email_digest(to_email),
            subject=subject,
        )
