"""Production e-mail adapter for the Resend HTTP API (#1821).

``EMAIL_ADAPTER=resend`` was documented from the start but had no
implementation: the value fell through to the console adapter, so no
verification, password-reset or step-up mail was ever delivered. This adapter
sends the same mails as :class:`SmtpEmailAdapter` (the texts live in
:class:`TemplatedEmailAdapter`) through ``POST https://api.resend.com/emails``.

**What it logs.** Like the SMTP adapter: a digest of the recipient
(``to_sha256``), never the address; on failure the error type and the HTTP
status, never the response body — Resend's error message can quote the
recipient or the sender domain — and never the API key, which travels only in
the ``Authorization`` header of the request.
"""

from __future__ import annotations

import httpx
import structlog

from app.common.decoys import email_digest
from app.data_access.external.templated_email_adapter import TemplatedEmailAdapter

logger = structlog.get_logger()

RESEND_EMAILS_URL = "https://api.resend.com/emails"
#: Connect and read bound for one send. A mail is sent inside a request
#: (registration, password reset, step-up), so a stalled API must not hold it.
RESEND_TIMEOUT_SECONDS = 10.0


class ResendDeliveryError(Exception):
    """Resend refused or failed the send. Carries the HTTP status only — never the response body."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"Resend rejected the e-mail (HTTP {status_code})")
        self.status_code = status_code


class ResendEmailAdapter(TemplatedEmailAdapter):
    """Sends the system mails through the Resend HTTP API."""

    def __init__(self, api_key: str, from_email: str, *, transport: httpx.BaseTransport | None = None) -> None:
        if not api_key:
            msg = "ResendEmailAdapter needs an API key (RESEND_API_KEY)"
            raise ValueError(msg)
        self._api_key = api_key
        self._from_email = from_email
        self._transport = transport

    def _send(self, to_email: str, subject: str, html_body: str) -> None:
        payload = {"from": self._from_email, "to": [to_email], "subject": subject, "html": html_body}
        try:
            with httpx.Client(transport=self._transport, timeout=RESEND_TIMEOUT_SECONDS) as client:
                response = client.post(
                    RESEND_EMAILS_URL, json=payload, headers={"Authorization": f"Bearer {self._api_key}"}
                )
            if not response.is_success:
                raise ResendDeliveryError(response.status_code)
        except Exception as exc:
            logger.error(
                "email_send_failed",
                to_sha256=email_digest(to_email),
                subject=subject,
                error_type=type(exc).__name__,
                status_code=getattr(exc, "status_code", None),
            )
            raise
        logger.info("email_sent", to_sha256=email_digest(to_email), subject=subject)
