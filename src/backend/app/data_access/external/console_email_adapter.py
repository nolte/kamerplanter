import structlog

from app.domain.interfaces.email_service import IEmailService

logger = structlog.get_logger()


class ConsoleEmailAdapter(IEmailService):
    """Development email adapter that logs emails to console."""

    def send_verification_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None:
        url = f"{frontend_url}/verify-email/{token}"
        logger.info(
            "email_verification",
            to=to_email,
            name=display_name,
            verification_url=url,
        )

    def send_password_reset_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None:
        url = f"{frontend_url}/password-reset/{token}"
        logger.info(
            "email_password_reset",
            to=to_email,
            name=display_name,
            reset_url=url,
        )
