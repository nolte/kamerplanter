"""Renders the duplicate-registration notice mail (REQ-023 §3.2, SEC-H-009).

German is the canonical text and English its mirror, following the project's
documentation convention (DOCS.md) and the locale-keyed label tables the print
engine already uses. The recipient owns an account here, so their stored
``locale`` picks the variant; anything unknown falls back to German, the
product default.

What the mail deliberately does **not** carry is the point of the module, so it
is spelled out rather than left to the reader of the strings below:

* **Not the display name the caller submitted.** It is attacker-chosen free
  text going into a third party's inbox; echoing it turns an informational
  notice into a message channel. Same reasoning as
  ``PrivacyService._notify_email_change_target``.
* **Not the submitted password, not the client IP, not a timestamp.** None of it
  helps the recipient act, all of it either leaks the sender's own data or
  invites the recipient to act on an unverified claim.
* **Nothing about the account itself** — no display name, no last login, no
  creation date. The trigger is an anonymous request; the mail must not become a
  way to read an account out of an inbox one happens to control.
* **No token and no one-click action.** Nothing happened that needs undoing.

What it does carry is one sentence of fact, the explicit statement that nothing
changed, and two links built from the operator-configured ``frontend_url`` —
sign-in and password reset — so a recipient who forgot they had an account can
get back in without replying to the mail.
"""

from html import escape

#: Locale used when the recipient's is unknown or unsupported.
DEFAULT_LOCALE = "de"

SUBJECTS: dict[str, str] = {
    "de": "Kamerplanter — Registrierungsversuch mit deiner E-Mail-Adresse",
    "en": "Kamerplanter — someone tried to register with your email address",
}

#: ``{login_url}`` and ``{reset_url}`` are the only substitutions, and both are
#: derived from configuration, never from request input.
BODIES: dict[str, str] = {
    "de": (
        "<h2>Jemand wollte ein Konto mit deiner E-Mail-Adresse anlegen</h2>"
        "<p>Bei Kamerplanter wurde versucht, ein neues Konto mit dieser "
        "E-Mail-Adresse zu registrieren. Weil die Adresse hier bereits ein Konto "
        "hat, wurde <strong>kein zweites Konto angelegt</strong>. An deinem Konto "
        "hat sich nichts geändert: dein Passwort gilt unverändert weiter, und es "
        "wurde kein Passwort geprüft oder gesetzt.</p>"
        "<p>Warst du das selbst, dann melde dich einfach mit dieser Adresse an: "
        '<a href="{login_url}">Anmelden</a>. Hast du dein Passwort vergessen, '
        'setze es hier neu: <a href="{reset_url}">Passwort zurücksetzen</a>.</p>'
        "<p>Warst du das nicht, musst du nichts tun. Wir können dir nicht sagen, "
        "wer den Versuch unternommen hat — die Registrierung erfordert keine "
        "Anmeldung. Wenn du dieses Passwort auch anderswo verwendest, ändere es "
        "dort besser.</p>"
        "<p>Diese Nachricht wird höchstens einmal pro Tag verschickt, auch wenn "
        "es mehrere Versuche gab.</p>"
    ),
    "en": (
        "<h2>Someone tried to create an account with your email address</h2>"
        "<p>Somebody attempted to register a new Kamerplanter account with this "
        "email address. Because the address already has an account here, "
        "<strong>no second account was created</strong>. Nothing about your "
        "account changed: your password still applies, and no password was "
        "checked or set.</p>"
        "<p>If that was you, simply sign in with this address: "
        '<a href="{login_url}">Sign in</a>. If you forgot your password, reset '
        'it here: <a href="{reset_url}">Reset password</a>.</p>'
        "<p>If it was not you, there is nothing you need to do. We cannot tell "
        "you who made the attempt — registration requires no sign-in. If you "
        "reuse this password elsewhere, change it there.</p>"
        "<p>This message is sent at most once a day, however many attempts "
        "there were.</p>"
    ),
}


class RegistrationNoticeEngine:
    """Builds subject and HTML body of the duplicate-registration notice."""

    def render(self, locale: str | None, frontend_url: str) -> tuple[str, str]:
        """Return ``(subject, html_body)`` for the recipient's locale.

        Args:
            locale: The recipient's stored locale. Unknown values fall back to
                :data:`DEFAULT_LOCALE`.
            frontend_url: Operator-configured base URL of the web app; the only
                value interpolated into the body.

        Returns:
            Subject line and ready-to-send HTML body.
        """
        language = locale if locale in BODIES else DEFAULT_LOCALE
        base = escape(frontend_url.rstrip("/"), quote=True)
        body = BODIES[language].format(
            login_url=f"{base}/login",
            reset_url=f"{base}/password-reset",
        )
        return SUBJECTS[language], body
