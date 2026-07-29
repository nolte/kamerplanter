"""The frontend CSP entrypoint must never widen the policy beyond one origin (#777).

``docker-entrypoint.d/30-error-tracking-csp.sh`` rewrites the shipped
Content-Security-Policy when a DSN is configured, appending the tracker's ingest
origin to ``connect-src``. The value it splices in comes from an environment
variable, and it reaches a *security header* through a ``sed`` replacement.

Whoever sets ``SENTRY_DSN`` already controls the deployment, so this is not a
privilege boundary. It is a robustness one: an early version of the script
extracted the host with ``s|/.*$||``, which strips everything after the first
slash — and a DSN carrying no path at all (``https://host; script-src *``)
therefore put every character after the host straight into the policy. The
result was a live page whose CSP had silently grown ``script-src *``.

These cases run the real script against a temporary copy of the real header
file, because the defect lived in shell quoting that no amount of reading the
Python side would have surfaced.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

# .../src/backend/tests/unit/entrypoints/<this file> -> repo root is five
# levels up plus one for the file itself.
_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCRIPT = _REPO_ROOT / "src" / "frontend" / "docker-entrypoint.d" / "30-error-tracking-csp.sh"
_HEADERS = _REPO_ROOT / "src" / "frontend" / "nginx-security-headers.inc"


def _run(tmp_path: Path, dsn: str | None) -> str:
    """Run the entrypoint against a copy of the shipped header file, return it."""
    headers = tmp_path / "nginx-security-headers.inc"
    shutil.copyfile(_HEADERS, headers)

    # The script hard-codes the container path; retarget it at the copy so the
    # real logic runs unmodified.
    script = tmp_path / "entrypoint.sh"
    script.write_text(
        _SCRIPT.read_text(encoding="utf-8").replace("/etc/nginx/conf.d/nginx-security-headers.inc", str(headers)),
        encoding="utf-8",
    )

    env = {"PATH": "/usr/bin:/bin"}
    if dsn is not None:
        env["SENTRY_DSN"] = dsn
    subprocess.run(["sh", str(script)], env=env, check=True, capture_output=True)  # noqa: S603, S607
    return headers.read_text(encoding="utf-8")


def _connect_src(headers: str) -> str:
    """Return the ``connect-src`` directive out of the CSP header line.

    The file carries several quoted headers; picking the first quoted string
    would read Strict-Transport-Security instead.
    """
    for line in headers.splitlines():
        if not line.startswith("add_header Content-Security-Policy"):
            continue
        for directive in line.split('"')[1].split(";"):
            if directive.strip().startswith("connect-src"):
                return directive.strip()
    raise AssertionError(f"no connect-src directive found in:\n{headers}")


@pytest.fixture
def script_available() -> None:
    # Deliberately an assertion, not a skip. A skip here would make a wrong path
    # look like a green run — which is exactly what happened while writing this
    # file, and is the failure mode #814 was about.
    assert _SCRIPT.exists(), f"entrypoint script not found at {_SCRIPT}"
    assert _HEADERS.exists(), f"header file not found at {_HEADERS}"


@pytest.mark.usefixtures("script_available")
class TestDefaultIsUntouched:
    def test_no_dsn_leaves_the_shipped_policy_exactly_as_built(self, tmp_path: Path) -> None:
        # The optionality contract at the CSP layer: a deployment without a
        # tracker must not carry a weakened header.
        assert _run(tmp_path, None) == _HEADERS.read_text(encoding="utf-8")

    def test_empty_dsn_is_treated_as_absent(self, tmp_path: Path) -> None:
        assert _run(tmp_path, "") == _HEADERS.read_text(encoding="utf-8")


@pytest.mark.usefixtures("script_available")
class TestConfiguredOrigin:
    def test_the_ingest_origin_is_appended_without_the_key(self, tmp_path: Path) -> None:
        policy = _run(tmp_path, "https://publickey@glitchtip.example.org/1")

        assert _connect_src(policy) == "connect-src 'self' https://glitchtip.example.org"
        # The DSN's public key is not a secret, but it has no business in a
        # header every visitor reads.
        assert "publickey" not in policy

    def test_a_port_survives(self, tmp_path: Path) -> None:
        policy = _run(tmp_path, "https://k@tracker.internal:9000/2")

        assert _connect_src(policy) == "connect-src 'self' https://tracker.internal:9000"


@pytest.mark.usefixtures("script_available")
@pytest.mark.parametrize(
    "dsn",
    [
        # The exact shape that used to inject: no path, so nothing stripped it.
        "https://evil.example; script-src *",
        "https://key@evil.example; script-src *",
        # A scheme the SDK cannot post to has no business in connect-src.
        "javascript:alert(1)",
        "not-a-url-at-all",
        # A quote would end the header value early.
        'https://evil.example" always; add_header X-Test "x',
    ],
)
class TestMalformedDsnDegradesSafely:
    def test_policy_is_left_untouched(self, tmp_path: Path, dsn: str) -> None:
        # A malformed DSN must degrade to "tracking does not reach the server",
        # never to "the page's CSP quietly grew a directive".
        assert _run(tmp_path, dsn) == _HEADERS.read_text(encoding="utf-8")
