from abc import ABC, abstractmethod


class IEmailService(ABC):
    @abstractmethod
    def send_verification_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None: ...

    @abstractmethod
    def send_password_reset_email(self, to_email: str, display_name: str, token: str, frontend_url: str) -> None: ...
