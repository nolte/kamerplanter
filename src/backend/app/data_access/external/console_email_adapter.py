import structlog

from app.common.decoys import email_digest
from app.config.settings import settings
from app.domain.interfaces.email_service import IEmailService

logger = structlog.get_logger()


class ConsoleEmailAdapter(IEmailService):
    """Development email adapter that logs emails to console instead of sending them.

    The recipient is logged as a digest (``to_sha256``), never the address
    (#1773 review GDPR-004): a log stream has no retention rule of its own. The
    recipient's display name is never logged either.

    **The verification / password-reset link is logged only when
    ``settings.debug`` is true (#1795).** Its token takes over the account (a
    reset link sets a new password), and this adapter is not only a development
    tool: ``EMAIL_ADAPTER`` defaults to ``console`` and the Helm chart sets none,
    so a production install without SMTP ran it and wrote every reset token into
    the cluster's logs. With ``debug`` a local operator can still complete a
    registration or a reset from the log; without it the line states the mail
    was not delivered (``url_logged=False``) and carries no token. The API warns
    once at startup in that configuration (``app.main.warn_if_console_email_adapter``)
    rather than refusing to start, which would break every Helm install without SMTP.
    """

    def send_verification_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None:
        if not settings.debug:
            logger.info("email_verification", to_sha256=email_digest(to_email), url_logged=False, delivered=False)
            return
        url = f"{frontend_url}/verify-email/{token}"
        logger.info("email_verification", to_sha256=email_digest(to_email), url_logged=True, verification_url=url)

    def send_password_reset_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None:
        if not settings.debug:
            logger.info("email_password_reset", to_sha256=email_digest(to_email), url_logged=False, delivered=False)
            return
        url = f"{frontend_url}/password-reset/{token}"
        logger.info("email_password_reset", to_sha256=email_digest(to_email), url_logged=True, reset_url=url)

    def send_notification_email(self, to_email: str, subject: str, html_body: str) -> None:
        logger.info(
            "email_notification",
            to_sha256=email_digest(to_email),
            subject=subject,
        )
