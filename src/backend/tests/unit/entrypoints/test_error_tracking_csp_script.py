"""The frontend CSP entrypoint must never widen the policy beyond one origin (#777, #3025 W-21).

``docker-entrypoint.d/30-error-tracking-csp.sh`` derives the tracker's ingest origin from
``SENTRY_DSN`` and writes it as the one entry of the nginx ``map`` that feeds
``${kp_csp_connect_extra}`` in the shipped Content-Security-Policy's ``connect-src``. The value
comes from an environment variable and reaches a *security header* through nginx configuration.

Whoever sets ``SENTRY_DSN`` already controls the deployment, so this is not a privilege boundary.
It is a robustness one: an early version of the script extracted the host with ``s|/.*$||``, which
strips everything after the first slash — and a DSN carrying no path at all
(``https://host; script-src *``) therefore put every character after the host straight into the
policy. The result was a live page whose CSP had silently grown ``script-src *``.

Until #3025 the script rewrote the header file in ``/etc/nginx/conf.d`` in place. In a Helm
install that directory is a read-only ConfigMap and ``/docker-entrypoint.d`` is suppressed, so the
script never ran and error tracking was CSP-blocked in every Kubernetes release. It now writes into
a runtime directory (``KP_NGINX_RUNTIME_DIR``) that the chart's init container fills.

These cases run the real script into a temporary runtime directory and compose the header the way
nginx does — the map's ``default`` value substituted for the variable in the real header file —
because the defect lived in shell quoting that no amount of reading the Python side would have
surfaced.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

# .../src/backend/tests/unit/entrypoints/<this file> -> repo root is five
# levels up plus one for the file itself.
_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCRIPT = _REPO_ROOT / "src" / "frontend" / "docker-entrypoint.d" / "30-error-tracking-csp.sh"
_HEADERS = _REPO_ROOT / "src" / "frontend" / "nginx-security-headers.inc"

_OUT_NAME = "csp-connect-src.conf"
_VARIABLE = "${kp_csp_connect_extra}"
# The only line nginx may read from the generated file: one map default with a quoted value that
# cannot end the string early.
_MAP_DEFAULT = re.compile(r'^default "([^"]*)";$')


def _run(runtime_dir: Path, dsn: str | None) -> subprocess.CompletedProcess[str]:
    env = {"PATH": "/usr/bin:/bin", "KP_NGINX_RUNTIME_DIR": str(runtime_dir)}
    if dsn is not None:
        env["SENTRY_DSN"] = dsn
    return subprocess.run(  # noqa: S603
        ["sh", str(_SCRIPT)],  # noqa: S607
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def _map_value(runtime_dir: Path) -> str:
    """The value nginx assigns to the variable: the map default, or "" without a file."""
    out = runtime_dir / _OUT_NAME
    if not out.exists():
        return ""
    lines = [line for line in out.read_text(encoding="utf-8").splitlines() if not line.startswith("#")]
    assert len(lines) == 1, f"the generated map file must hold exactly one entry, got {lines!r}"
    match = _MAP_DEFAULT.match(lines[0])
    assert match, f"the generated map entry is not a plain quoted default: {lines[0]!r}"
    return match.group(1)


def _connect_src(runtime_dir: Path) -> str:
    """``connect-src`` of the CSP as nginx sends it after the script ran."""
    for line in _HEADERS.read_text(encoding="utf-8").splitlines():
        if not line.startswith("add_header Content-Security-Policy"):
            continue
        policy = line.split('"')[1].replace(_VARIABLE, _map_value(runtime_dir))
        for directive in policy.split(";"):
            if directive.strip().startswith("connect-src"):
                return directive.strip()
    raise AssertionError(f"no connect-src directive found in {_HEADERS}")


@pytest.fixture(autouse=True)
def _script_available() -> None:
    # Deliberately an assertion, not a skip. A skip here would make a wrong path
    # look like a green run — the failure mode #814 was about.
    assert _SCRIPT.exists(), f"entrypoint script not found at {_SCRIPT}"
    assert _HEADERS.exists(), f"header file not found at {_HEADERS}"
    assert _VARIABLE in _HEADERS.read_text(encoding="utf-8"), "the CSP no longer reads the map variable"


class TestDefaultIsUntouched:
    def test_no_dsn_writes_nothing_and_keeps_connect_src_self(self, tmp_path: Path) -> None:
        # The optionality contract at the CSP layer: a deployment without a
        # tracker must not carry a weakened header.
        _run(tmp_path, None)
        assert not (tmp_path / _OUT_NAME).exists()
        assert _connect_src(tmp_path) == "connect-src 'self'"

    def test_empty_dsn_is_treated_as_absent(self, tmp_path: Path) -> None:
        _run(tmp_path, "")
        assert not (tmp_path / _OUT_NAME).exists()

    def test_a_stale_origin_from_an_earlier_start_is_removed(self, tmp_path: Path) -> None:
        # A restarted container keeps its filesystem: a DSN removed since the last start must
        # not leave the old origin in the policy.
        _run(tmp_path, "https://k@old-tracker.example/1")
        assert _connect_src(tmp_path) == "connect-src 'self' https://old-tracker.example"
        _run(tmp_path, None)
        assert _connect_src(tmp_path) == "connect-src 'self'"

    def test_an_origin_is_removed_when_the_dsn_turns_malformed(self, tmp_path: Path) -> None:
        _run(tmp_path, "https://k@old-tracker.example/1")
        _run(tmp_path, "https://evil.example; script-src *")
        assert _connect_src(tmp_path) == "connect-src 'self'"


class TestConfiguredOrigin:
    def test_the_ingest_origin_is_appended_without_the_key(self, tmp_path: Path) -> None:
        _run(tmp_path, "https://publickey@glitchtip.example.org/1")

        assert _connect_src(tmp_path) == "connect-src 'self' https://glitchtip.example.org"
        # The DSN's public key is not a secret, but it has no business in a
        # header every visitor reads.
        assert "publickey" not in (tmp_path / _OUT_NAME).read_text(encoding="utf-8")

    def test_a_port_survives(self, tmp_path: Path) -> None:
        _run(tmp_path, "https://k@tracker.internal:9000/2")

        assert _connect_src(tmp_path) == "connect-src 'self' https://tracker.internal:9000"

    def test_a_missing_runtime_directory_is_created(self, tmp_path: Path) -> None:
        runtime = tmp_path / "not-yet"
        _run(runtime, "https://k@tracker.example/3")

        assert _connect_src(runtime) == "connect-src 'self' https://tracker.example"


@pytest.mark.parametrize(
    "dsn",
    [
        # The exact shape that used to inject: no path, so nothing stripped it.
        "https://evil.example; script-src *",
        "https://key@evil.example; script-src *",
        # A scheme the SDK cannot post to has no business in connect-src.
        "javascript:alert(1)",
        "not-a-url-at-all",
        # A quote would end the header value (or the nginx string) early.
        'https://evil.example" always; add_header X-Test "x',
        # A newline would add a second map entry.
        "https://evil.example\ndefault x",
        # nginx variable syntax and non-ASCII hosts are no origin.
        "https://${evil}.example/1",
        "https://ex{a}mple.org/1",
        "https://k@tr\u00e4cker.example/1",
        # A port is digits only, and a bare colon is no host.
        "https://k@:/1",
        "https://k@tracker.example:9x/1",
        "https://k@tracker.example:/1",
    ],
)
class TestMalformedDsnDegradesSafely:
    def test_policy_is_left_at_self(self, tmp_path: Path, dsn: str) -> None:
        # A malformed DSN must degrade to "tracking does not reach the server",
        # never to "the page's CSP quietly grew a directive".
        _run(tmp_path, dsn)
        assert not (tmp_path / _OUT_NAME).exists()
        assert _connect_src(tmp_path) == "connect-src 'self'"
