from abc import ABC, abstractmethod


class EmailUndeliverableError(Exception):
    """The adapter cannot deliver this mail — it is configured not to (e.g. the console adapter outside debug).

    Raised instead of returning quietly where the caller's answer depends on the
    mail arriving: a step-up code that is never delivered must not be answered
    with "sent" (/code-review of #1862).
    """


class IEmailService(ABC):
    @abstractmethod
    def send_verification_email(self, to_email: str, token: str, frontend_url: str) -> None:
        """Mail the account-verification link. The address is unverified: no requester-chosen text (#1856)."""

    @abstractmethod
    def send_password_reset_email(self, to_email: str, token: str, frontend_url: str) -> None:
        """Mail the reset link. The address may be unverified: no requester-chosen text (#1856)."""

    def send_notification_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
    ) -> None:
        """Send a generic notification email. Default raises NotImplementedError."""
        msg = f"{self.__class__.__name__} does not support notification emails"
        raise NotImplementedError(msg)

    def send_email_change_email(self, to_email: str, token: str, frontend_url: str) -> None:
        """Mail the link that confirms an e-mail change to the new address (#1848). Default raises NotImplementedError.

        The link opens ``{frontend_url}/email-change/{token}``, whose page calls
        ``POST /privacy/email-change/confirm``. The address is not verified yet,
        so the mail carries no requester-chosen text (#1856).
        """
        msg = f"{self.__class__.__name__} does not support e-mail change mails"
        raise NotImplementedError(msg)

    def send_step_up_code_email(self, to_email: str, display_name: str, code: str, purpose: str) -> None:
        """Send the one-time step-up code (#1815). Default raises NotImplementedError.

        The code confirms an irreversible act or a credential change of an account
        without a local password; it is valid for ten minutes and must never be
        logged outside a local debug setup. *purpose* names the act the code is for
        (fixed text from ``step_up_service.CODE_PURPOSES``, review SEC-003), so the
        owner sees what they — or someone in their session — is about to confirm.
        """
        msg = f"{self.__class__.__name__} does not support step-up code emails"
        raise NotImplementedError(msg)
