"""The mail texts every delivering e-mail adapter sends (SMTP, Resend, #1821).

One place for the bodies, so a delivering adapter only decides *how* a message
leaves the process (:meth:`TemplatedEmailAdapter._send`), never *what* it says.
Until #1821 the texts lived in ``SmtpEmailAdapter``; a second adapter copying
them would have been the drift the step-up mail's escaping (#1815) shows: that
body escapes the display name, and a copy made before that change would not.
"""

from __future__ import annotations

from abc import abstractmethod
from html import escape

from app.domain.interfaces.email_service import IEmailService


class TemplatedEmailAdapter(IEmailService):
    """An ``IEmailService`` that renders the system mails and hands each to :meth:`_send`."""

    @abstractmethod
    def _send(self, to_email: str, subject: str, html_body: str) -> None:
        """Deliver one HTML mail, or raise. Logs a digest of the recipient, never the address."""

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

    def send_password_reset_email(self, to_email: str, token: str, frontend_url: str) -> None:
        # No display name: a reset can be requested for an account registered under
        # a stranger's address, so the recipient may never have confirmed it (#1856).
        url = f"{frontend_url}/password-reset/{token}"
        html = f"""
        <h2>Password Reset</h2>
        <p>Hello,</p>
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
