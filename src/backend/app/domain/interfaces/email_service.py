from abc import ABC, abstractmethod


class IEmailService(ABC):
    @abstractmethod
    def send_verification_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None: ...

    @abstractmethod
    def send_password_reset_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None: ...

    def send_notification_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
    ) -> None:
        """Send a generic notification email. Default raises NotImplementedError."""
        msg = f"{self.__class__.__name__} does not support notification emails"
        raise NotImplementedError(msg)
