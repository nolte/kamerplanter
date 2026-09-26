import structlog

from app.common.decoys import email_digest
from app.config.settings import settings
from app.domain.interfaces.email_service import EmailUndeliverableError, IEmailService

logger = structlog.get_logger()


class ConsoleEmailAdapter(IEmailService):
    """Development email adapter that logs emails to console instead of sending them.

    The recipient is logged as a digest (``to_sha256``), never the address
    (#1773 review GDPR-004): a log stream has no retention rule of its own. The
    recipient's display name is never logged either.

    **The verification / password-reset link — and the step-up code (#1815) — is logged only when
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

    def send_verification_email(self, to_email: str, token: str, frontend_url: str) -> None:
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

    def send_email_change_email(self, to_email: str, token: str, frontend_url: str) -> None:
        # The link moves the account onto the new address (#1848): the #1795 rule.
        if not settings.debug:
            logger.info("email_change", to_sha256=email_digest(to_email), url_logged=False, delivered=False)
            return
        url = f"{frontend_url}/email-change/{token}"
        logger.info("email_change", to_sha256=email_digest(to_email), url_logged=True, email_change_url=url)

    def send_step_up_code_email(self, to_email: str, display_name: str, code: str, purpose: str) -> None:
        # The code confirms an account erasure or a credential change (#1815) — the
        # same weight as a reset link, so the same #1795 rule: logged only under
        # ``settings.debug``, otherwise the line says it was not delivered.
        if not settings.debug:
            logger.info(
                "email_step_up_code",
                to_sha256=email_digest(to_email),
                purpose=purpose,
                code_logged=False,
                delivered=False,
            )
            # Unlike the reset link, the caller answers "code sent" — which would
            # be false (/code-review of #1862). Refuse, so the route answers 503.
            raise EmailUndeliverableError("The console e-mail adapter does not deliver step-up codes outside debug.")
        logger.info(
            "email_step_up_code", to_sha256=email_digest(to_email), purpose=purpose, code_logged=True, step_up_code=code
        )

    def send_notification_email(self, to_email: str, subject: str, html_body: str) -> None:
        logger.info(
            "email_notification",
            to_sha256=email_digest(to_email),
            subject=subject,
        )
