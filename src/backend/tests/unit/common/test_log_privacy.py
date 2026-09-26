"""#1781 — what a log line may carry about a person: the shared helpers.

A log stream has no retention rule of its own (NFR-011): whatever it receives
outlives the account it names, the erasure that removed the account and the
erasure record proving it (R-06). ``app.common.log_privacy`` is the one home of
the helpers every log call uses instead of the raw value — the salted subject
reference, a redacted exception text and a truncated IP.

Every test calls the real helper, which reads ``settings`` at call time — the
same object the production call sites read.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from app.common import log_privacy
from app.common.decoys import email_digest
from app.common.log_privacy import (
    log_subject,
    loggable_error,
    loggable_ip,
    loggable_path,
    loggable_url_text,
    register_route_source,
)
from app.config.settings import settings
from app.domain.engines.erasure_engine import UNAVAILABLE_LOG_SUBJECT, ErasureEngine

_SALT = "s" * 40


@pytest.fixture
def salted(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setattr(settings, "log_pseudonym_salt", _SALT)
    return _SALT


# ── log_subject ─────────────────────────────────────────────────────────


def test_log_subject_is_the_erasure_engine_reference(salted: str) -> None:
    assert log_subject("12345") == ErasureEngine.log_subject("12345", salted)
    assert "12345" not in (log_subject("12345") or "")


@pytest.mark.parametrize("empty", [None, ""])
def test_log_subject_of_no_key_is_none(salted: str, empty: str | None) -> None:
    assert log_subject(empty) is None


def test_log_subject_without_salt_is_the_unavailable_constant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "log_pseudonym_salt", "")
    assert log_subject("12345") == UNAVAILABLE_LOG_SUBJECT


def test_log_subject_reads_the_salt_at_call_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "log_pseudonym_salt", "a" * 32)
    first = log_subject("12345")
    monkeypatch.setattr(settings, "log_pseudonym_salt", "b" * 32)
    assert log_subject("12345") != first


# ── loggable_error ──────────────────────────────────────────────────────


def test_loggable_error_replaces_the_subject_key(salted: str) -> None:
    text = loggable_error(LookupError("User 12345 not found"), user_key="12345")
    assert "12345" not in text
    assert ErasureEngine.log_subject("12345", salted) in text
    assert text.startswith("User ")


def test_loggable_error_masks_an_export_bundle_key_of_any_account(salted: str) -> None:
    text = loggable_error(OSError("No such file: '/data/privacy/exports/99999/abc.json'"))
    assert "99999" not in text
    assert "abc.json" in text


def test_loggable_error_masks_every_email_address(salted: str) -> None:
    exc = RuntimeError("recipients refused: {'Alice.Doe@Example.org': (550, b'no'), 'bob@x.io': (550, b'no')}")
    text = loggable_error(exc)
    assert "Alice.Doe@Example.org" not in text
    assert "bob@x.io" not in text
    assert f"<email:{email_digest('Alice.Doe@Example.org')}>" in text
    assert f"<email:{email_digest('bob@x.io')}>" in text
    assert "550" in text, "the rest of the text is what an operator needs"


def test_loggable_error_strips_url_query_strings(salted: str) -> None:
    exc = RuntimeError(
        "Client error '401 Unauthorized' for url "
        "'https://api.openweathermap.org/data/3.0/onecall?lat=52.52&lon=13.40&appid=SECRET'"
    )
    text = loggable_error(exc)
    assert "SECRET" not in text
    assert "52.52" not in text
    assert "https://api.openweathermap.org/data/3.0/onecall?<redacted>" in text
    assert "401 Unauthorized" in text


def test_loggable_error_keeps_a_url_without_query(salted: str) -> None:
    text = loggable_error("GET http://backend:8000/api/v1/health failed")
    assert text == "GET http://backend:8000/api/v1/health failed"


@pytest.mark.parametrize(
    ("raw", "masked"),
    [
        ("Error 111 connecting to redis://user:pw-1795@redis:6379/0.", "redis://<redacted>@redis:6379/0."),
        ("cannot reach redis://:pw-1795@redis:6379/0", "redis://<redacted>@redis:6379/0"),
        ("login failed for smtp://mailer@smtp.example:587", "smtp://<redacted>@smtp.example:587"),
        ("apprise mailto://alice:pw-1795@gmail.com failed", "mailto://<redacted>@gmail.com"),
    ],
    ids=["user-password", "password-only", "user-only", "mailto"],
)
def test_loggable_error_masks_url_userinfo(salted: str, raw: str, masked: str) -> None:
    """#1795: a DSN in a connection error carries its password in the userinfo."""
    text = loggable_error(raw)
    assert "pw-1795" not in text
    assert "alice" not in text
    assert "mailer" not in text
    assert masked in text


def test_loggable_error_accepts_a_plain_string(salted: str) -> None:
    assert loggable_error("disk full") == "disk full"


# ── loggable_ip ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "truncated"),
    [
        ("192.168.1.42", "192.168.1.0"),
        ("2001:0db8:85a3:1234:5678:8a2e:0370:7334", "2001:db8:85a3::"),
        ("::1", "::"),
        ("not-an-ip", "0.0.0.0"),
        ("", "0.0.0.0"),
    ],
)
def test_loggable_ip_is_the_r03_truncation(raw: str, truncated: str) -> None:
    assert loggable_ip(raw) == truncated


def test_loggable_ip_of_none_is_none() -> None:
    assert loggable_ip(None) is None


def test_the_ip_retention_task_uses_the_same_truncation() -> None:
    """One implementation: what the DB keeps after 7 days is what a log line carries."""
    from app.tasks.auth_tasks import _anonymize_ip

    assert _anonymize_ip is loggable_ip
    for raw in ("192.168.1.42", "2001:db8:85a3:1:2:3:4:5", "garbage"):
        assert _anonymize_ip(raw) == loggable_ip(raw)


# ── loggable_url_text ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            'HTTP Request: GET https://api.openweathermap.org/data/2.5/forecast?lat=52.5&appid=K "HTTP/1.1 200 OK"',
            'HTTP Request: GET https://api.openweathermap.org/data/2.5/forecast?<redacted> "HTTP/1.1 200 OK"',
        ),
        (
            'HTTP Request: GET https://u:p@perenual.com/api/species-list?key=K "HTTP/1.1 200 OK"',
            'HTTP Request: GET https://<redacted>@perenual.com/api/species-list?<redacted> "HTTP/1.1 200 OK"',
        ),
        (
            'http://arangodb:8529 "GET /_db/kp/_api/cursor?batch=1 HTTP/1.1" 201 None',
            'http://arangodb:8529 "GET /_db/kp/_api/cursor?<redacted> HTTP/1.1" 201 None',
        ),
        ("Starting new HTTP connection (1): arangodb:8529", "Starting new HTTP connection (1): arangodb:8529"),
    ],
    ids=["httpx-query", "httpx-userinfo", "urllib3-target", "no-url"],
)
def test_loggable_url_text_masks_userinfo_and_queries(raw: str, expected: str) -> None:
    assert loggable_url_text(raw) == expected


# ── loggable_path ───────────────────────────────────────────────────────


_TEMPLATES = (
    "/api/v1/attachments/token/{token}",
    "/api/v1/t/{tenant_slug}/plant-instances/{key}",
    "/api/v1/auth/password-reset/confirm",
    "/api/health",
)


@pytest.fixture
def routes() -> Iterator[None]:
    saved = (log_privacy._route_source, log_privacy._literal_segments)
    register_route_source(lambda: _TEMPLATES)
    yield
    log_privacy._route_source, log_privacy._literal_segments = saved


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("/api/v1/attachments/token/abc.def", "/api/v1/attachments/token/{}"),
        ("/api/v1/t/max-mustermann/plant-instances/123", "/api/v1/t/{}/plant-instances/{}"),
        ("/api/v1/auth/password-reset/confirm?token=abc", "/api/v1/auth/password-reset/confirm?<redacted>"),
        ("/api/health", "/api/health"),
        ("/api/v1/", "/api/v1/"),
        ("/", "/"),
        ("/api/v1/unknown/thing", "/api/v1/{}/{}"),
    ],
)
def test_loggable_path_keeps_only_route_literals(routes: None, raw: str, expected: str) -> None:
    assert loggable_path(raw) == expected


def test_loggable_path_reads_the_source_once(routes: None) -> None:
    calls: list[int] = []

    def source() -> tuple[str, ...]:
        calls.append(1)
        return _TEMPLATES

    register_route_source(source)
    loggable_path("/api/v1/t/x")
    loggable_path("/api/v1/t/y")
    assert len(calls) == 1


def test_loggable_path_without_a_source_keeps_only_the_api_prefix(routes: None) -> None:
    log_privacy._route_source, log_privacy._literal_segments = None, None
    assert loggable_path("/api/v2/attachments/token/abc?x=1") == "/api/v2/{}/{}/{}?<redacted>"


def test_loggable_path_with_a_failing_source_keeps_only_the_api_prefix(routes: None) -> None:
    def broken() -> tuple[str, ...]:
        raise RuntimeError("router walk failed")

    register_route_source(broken)
    assert loggable_path("/api/v1/t/max-mustermann/plant-instances/1") == "/api/v1/{}/{}/{}/{}"


# ── loggable_error hardening (#1796) ────────────────────────────────────


def test_loggable_error_masks_a_unicode_address_whole(salted: str) -> None:
    text = loggable_error("refused: müller@x.de and user@bücher.de")
    assert "müller" not in text
    assert "mü" not in text
    assert "bücher" not in text
    assert text.count("<email:") == 2, text


@pytest.mark.parametrize(
    "raw",
    [
        "GET https://h/p#frag?appid=K1SECRET failed",
        "GET https://h/p?appid=K1SECRET#frag failed",
        "redirect to https://h/cb#access_token=K1SECRET",
    ],
)
def test_loggable_error_masks_fragment_and_query(salted: str, raw: str) -> None:
    text = loggable_error(raw)
    assert "K1SECRET" not in text
    assert "frag" not in text
    assert "https://h/" in text


def test_loggable_error_masks_an_address_at_the_end_of_an_overlong_run(salted: str) -> None:
    """A run of address characters longer than an RFC local part still loses its address."""
    text = loggable_error("x" * 100 + ".john.doe@example.org")
    assert "john.doe@example.org" not in text
    assert "<email:" in text


def test_loggable_error_caps_the_text_with_a_marker(salted: str) -> None:
    text = loggable_error("x" * 50_000)
    assert len(text) < 5_000
    assert text.endswith("chars>")
    assert "<truncated" in text


def test_loggable_error_masks_before_it_caps(salted: str) -> None:
    """An address straddling the cap is masked, not cut into a readable half."""
    text = loggable_error("y" * (log_privacy.MAX_LOGGABLE_TEXT - 6) + " alice@example.org tail")
    assert "alice" not in text


@pytest.mark.parametrize(
    "unit",
    ["a", "a.", "a@", "http://a", "a://", "@a.", "x" * 70 + "@"],
    ids=["run", "dots", "ats", "urls", "schemes", "domains", "long-local"],
)
def test_the_masking_is_linear(salted: str, unit: str) -> None:
    """200k characters of any adversarial shape mask in well under a second (was quadratic: 8k chars 0.85 s)."""
    import time

    text = unit * (200_000 // len(unit))
    started = time.perf_counter()
    log_privacy._mask_text(text)
    assert time.perf_counter() - started < 0.5


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("expired:https://fcm.googleapis.com/fcm/send/TOK", "expired:https://fcm.googleapis.com/<redacted>"),
        ("a https://h.example?x=TOK b", "a https://h.example/<redacted> b"),
        ("https://h.example", "https://h.example"),
        ("'https://h.example/p/TOK' and http://x/TOK2", "'https://h.example/<redacted>' and http://x/<redacted>"),
    ],
)
def test_mask_url_paths_keeps_scheme_and_host(raw: str, expected: str) -> None:
    assert log_privacy.mask_url_paths(raw) == expected


def test_mask_url_paths_is_linear() -> None:
    import time

    text = "http://a" * 25_000
    started = time.perf_counter()
    log_privacy.mask_url_paths(text)
    assert time.perf_counter() - started < 0.5


# ── review round: order, userinfo, case, bare targets (#1795/#1796 review) ──


_REVIEW_CASES = [
    # SEC-001: an address-shaped path segment must not swallow the URL before its query is masked.
    ("https://api.x.com/v1/u/alice@example.org/items?api_key=SECRET1", "SECRET1"),
    ("GET https://cdn.x.com/tile@2x.png?access_token=SECRET2", "SECRET2"),
    ("https://registry.x.com/pkg@1.2.3/index.js?token=SECRET3", "SECRET3"),
    ("https://x.com/cb?email=a@b.org&key=SECRET4", "SECRET4"),
    # SEC-004: a password containing ``@``.
    ("redis://:p@ss@valkey:6379/0", "ss@valkey"),
    ("redis://user:p@ss@w0rd@valkey:6379/0", "w0rd"),
    # SEC-005: upper-case scheme.
    ("HTTPS://API.X.COM/data?key=SECRET5", "SECRET5"),
    ("Http://h.example/p#access_token=SECRET5b", "SECRET5b"),
    # SEC-006: bare request targets in library exception texts.
    ("Max retries exceeded with url: /fcm/send/TOK?key=SECRET6 (Caused by NewConnectionError)", "SECRET6"),
    ('"GET /data/2.5/forecast?appid=SECRET7 HTTP/1.1" 401', "SECRET7"),
]


@pytest.mark.parametrize(("raw", "secret"), _REVIEW_CASES)
@pytest.mark.parametrize("redact", ["loggable_error", "loggable_text"])
def test_the_review_spellings_lose_their_secret(salted: str, redact: str, raw: str, secret: str) -> None:
    text = getattr(log_privacy, redact)(raw)
    assert secret not in text, text


def test_a_path_segment_with_an_at_keeps_the_host(salted: str) -> None:
    text = loggable_error("https://api.x.com/v1/u/alice@example.org/items?api_key=SECRET1")
    assert text.startswith("https://api.x.com/"), text


def test_the_bare_target_masking_leaves_source_lines_alone(salted: str) -> None:
    """Only the two library spellings are masked — a ``?`` in a traceback source line stays."""
    line = '    value = cache.get(key) if key else None  # what? "maybe"'
    assert log_privacy.loggable_text(line) == line


def test_a_plain_address_is_still_masked_after_the_reorder(salted: str) -> None:
    text = loggable_error("recipient bob.smith@example.org refused")
    assert "bob.smith" not in text
    assert "<email:" in text


@pytest.mark.parametrize("unit", ["a@a/", "x://a@", "with url: /a?", "GET /a?b HTTP/"])
def test_the_review_patterns_stay_linear(salted: str, unit: str) -> None:
    import time

    text = unit * (200_000 // len(unit))
    started = time.perf_counter()
    log_privacy._mask_text(text)
    assert time.perf_counter() - started < 0.5


# ── loggable_text over a rendered JSON line (#1837 review) ──────────────


@pytest.mark.parametrize(
    "value",
    [
        "refused:\nalice@example.org",
        "refused:\talice@example.org",
        "refused:\r\nalice@example.org",
        "refused:\x01alice@example.org",
    ],
)
def test_loggable_text_keeps_a_rendered_json_line_valid(salted: str, value: str) -> None:
    """The sink backstop sees structlog's rendered JSON, where ``\\n`` is two
    characters and its ``n`` is a local-part character. The address is masked
    and the escape stays whole, so the line still parses and keeps its text."""
    import json

    from app.common.log_privacy import loggable_text

    masked = loggable_text(json.dumps({"detail": value}, ensure_ascii=False))

    decoded = json.loads(masked)["detail"]
    assert "alice@example.org" not in masked
    assert decoded == value.replace("alice@example.org", f"<email:{email_digest('alice@example.org')}>")


def test_log_pseudonyms_are_keyed_with_the_log_salt_not_the_tombstone_salt(monkeypatch) -> None:
    """#1812: the tombstone salt can never rotate; the log pseudonyms follow the rotatable log salt only."""
    from app.common.decoys import email_digest

    monkeypatch.setattr(settings, "log_pseudonym_salt", "L" * 32)
    monkeypatch.setattr(settings, "erasure_tombstone_salt", "T" * 32)
    subject, digest = log_subject("12345"), email_digest("mira@example.org")

    monkeypatch.setattr(settings, "erasure_tombstone_salt", "U" * 32)
    assert (log_subject("12345"), email_digest("mira@example.org")) == (subject, digest)

    monkeypatch.setattr(settings, "log_pseudonym_salt", "M" * 32)
    assert log_subject("12345") != subject
    assert email_digest("mira@example.org") != digest
    assert subject == ErasureEngine.log_subject("12345", "L" * 32)
