"""#2127 (MT-031) — the ArangoDB scheme is a setting, and every client reads it.

Until #2127 seven places built ``f"http://{host}:{port}"`` themselves: the
connection class, two operator migrations, two audit scripts and two reach
seeders. An external database that terminates TLS could not be reached at all,
and a fix in one place would have left the other six on plain text.

Now :attr:`Settings.arangodb_url` is the one spelling. ``ARANGODB_SCHEME``
defaults to ``http`` — a deployment that sets nothing connects to exactly the
URL it connected to before — and accepts ``https``; anything else refuses to
load, without echoing the value. ``ARANGODB_HOST`` refuses a URL, so the scheme
cannot hide in the host and be silently overridden.

The sweep at the end reads every ``ArangoClient(...)`` construction in the
application, its operator scripts and the reach seeders by AST: each must take
its hosts from ``.arangodb_url``. Spellings it does NOT see: a client built
through ``getattr``/``importlib``, or by a helper in a file outside the swept
roots (the test support code, which talks to the CI database on purpose).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.config.settings import Settings, SettingsError, load_settings
from app.data_access.arango import connection as connection_module
from app.data_access.arango.connection import ArangoConnection

BACKEND = Path(__file__).resolve().parents[3]
REPO = BACKEND.parents[1]

#: Roots whose ArangoDB clients connect to an operator's database.
SWEPT_ROOTS = (BACKEND / "app", BACKEND / "scripts", REPO / "scripts" / "reach")


class TestTheDefaultIsUnchanged:
    def test_the_default_scheme_is_http(self) -> None:
        assert Settings().arangodb_scheme == "http"

    def test_the_default_url_is_the_one_every_client_built_before(self) -> None:
        settings = Settings(arangodb_host="kamerplanter-arangodb", arangodb_port=8529)
        assert settings.arangodb_url == "http://kamerplanter-arangodb:8529"


class TestTheSchemeIsASetting:
    def test_https_from_the_environment_reaches_the_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ARANGODB_SCHEME", "https")
        monkeypatch.setenv("ARANGODB_HOST", "arango.example.net")
        monkeypatch.setenv("ARANGODB_PORT", "18529")
        assert load_settings().arangodb_url == "https://arango.example.net:18529"

    @pytest.mark.parametrize("value", ["ftp", "HTTPS", "tcp", "ssl", "https://", ""])
    def test_an_unknown_scheme_refuses_to_load_and_names_the_variable(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        monkeypatch.setenv("ARANGODB_SCHEME", value)
        with pytest.raises(SettingsError, match="ARANGODB_SCHEME") as caught:
            load_settings()
        if value:
            assert repr(value) not in str(caught.value)

    @pytest.mark.parametrize(
        "host",
        ["https://arango.example.net", "arango.example.net/", "user:secret-value@arango.example.net"],
    )
    def test_a_url_in_the_host_refuses_to_load_without_echoing_it(
        self, monkeypatch: pytest.MonkeyPatch, host: str
    ) -> None:
        monkeypatch.setenv("ARANGODB_HOST", host)
        with pytest.raises(SettingsError, match="ARANGODB_HOST") as caught:
            load_settings()
        assert "secret-value" not in str(caught.value)
        assert host not in str(caught.value)

    @pytest.mark.parametrize("host", ["localhost", "kamerplanter-arangodb", "10.0.0.7", "db.example.net"])
    def test_a_bare_host_loads(self, host: str) -> None:
        assert Settings(arangodb_host=host).arangodb_host == host


@pytest.mark.allow_db_connection("connects a test double of ArangoClient, never a server")
class TestTheConnectionUsesTheSetting:
    @pytest.mark.parametrize(
        ("scheme", "expected"),
        [("http", "http://arango.example.net:8529"), ("https", "https://arango.example.net:8529")],
    )
    def test_the_client_is_built_on_the_configured_url(
        self, monkeypatch: pytest.MonkeyPatch, scheme: str, expected: str
    ) -> None:
        built: list[Any] = []

        def _client(**kwargs: Any) -> MagicMock:
            built.append(kwargs["hosts"])
            client = MagicMock()
            client.db.return_value.properties.return_value = {}
            return client

        monkeypatch.setattr(connection_module, "ArangoClient", _client)
        ArangoConnection(Settings(arangodb_host="arango.example.net", arangodb_scheme=scheme)).connect()
        assert built == [expected]


def _arango_client_calls(tree: ast.AST) -> list[ast.Call]:
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
        if name == "ArangoClient":
            calls.append(node)
    return calls


def _hosts_argument(call: ast.Call) -> ast.expr | None:
    for keyword in call.keywords:
        if keyword.arg == "hosts":
            return keyword.value
    return call.args[0] if call.args else None


def _reads_the_setting(node: ast.expr | None) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "arangodb_url"


class TestEveryClientReadsTheSetting:
    def test_the_sweep_finds_the_known_clients(self) -> None:
        """Seven constructions exist; a sweep that finds none would pass on anything."""
        found = [
            path
            for root in SWEPT_ROOTS
            for path in sorted(root.rglob("*.py"))
            if _arango_client_calls(ast.parse(path.read_text(encoding="utf-8")))
        ]
        assert BACKEND / "app" / "data_access" / "arango" / "connection.py" in found
        assert len(found) >= 7

    def test_every_client_takes_its_hosts_from_arangodb_url(self) -> None:
        offenders = []
        for root in SWEPT_ROOTS:
            for path in sorted(root.rglob("*.py")):
                for call in _arango_client_calls(ast.parse(path.read_text(encoding="utf-8"))):
                    if not _reads_the_setting(_hosts_argument(call)):
                        offenders.append(f"{path.relative_to(REPO)}:{call.lineno}")
        assert offenders == [], (
            "build the ArangoDB endpoint from Settings.arangodb_url, not from host and port "
            f"(an own scheme ignores ARANGODB_SCHEME, #2127): {offenders}"
        )

    def test_the_sweep_rejects_the_old_spelling(self) -> None:
        """Counter-probe on the expression the sweep checks: the pre-#2127 line fails it."""
        old = 'ArangoClient(hosts=f"http://{settings.arangodb_host}:{settings.arangodb_port}")'
        (call,) = _arango_client_calls(ast.parse(old))
        assert not _reads_the_setting(_hosts_argument(call))
        (call,) = _arango_client_calls(ast.parse("ArangoClient(hosts=settings.arangodb_url)"))
        assert _reads_the_setting(_hosts_argument(call))
