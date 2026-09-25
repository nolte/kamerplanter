"""``scripts/e2e_fernet_key.py`` — the E2E stack's generated Fernet key (#1838)."""

from __future__ import annotations

import ast
import importlib.util
import stat
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

_SCRIPT = Path(__file__).resolve().parents[5] / "scripts" / "e2e_fernet_key.py"


def _module():  # noqa: ANN202
    spec = importlib.util.spec_from_file_location("e2e_fernet_key", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_generated_key_is_accepted_by_fernet_and_stored_private(tmp_path: Path):
    mod = _module()
    key_file = tmp_path / ".e2e-secrets" / "fernet.key"

    key = mod.resolve(environ={}, key_file=key_file)

    Fernet(key.encode())  # the backend's EncryptionEngine constructs exactly this
    assert stat.S_IMODE(key_file.stat().st_mode) == 0o600
    assert key_file.read_text().strip() == key


def test_the_stored_key_is_reused_so_separate_up_calls_agree(tmp_path: Path):
    mod = _module()
    key_file = tmp_path / "fernet.key"

    assert mod.resolve(environ={}, key_file=key_file) == mod.resolve(environ={}, key_file=key_file)


def test_an_exported_key_wins_and_is_not_written(tmp_path: Path):
    mod = _module()
    key_file = tmp_path / "fernet.key"
    given = Fernet.generate_key().decode()

    assert mod.resolve(environ={"E2E_FERNET_KEY": given}, key_file=key_file) == given
    assert not key_file.exists()


def test_an_exported_value_that_is_not_a_key_is_refused(tmp_path: Path):
    mod = _module()

    with pytest.raises(SystemExit):
        mod.resolve(environ={"E2E_FERNET_KEY": "not-a-key"}, key_file=tmp_path / "fernet.key")


def test_two_working_copies_get_different_keys(tmp_path: Path):
    mod = _module()

    first = mod.resolve(environ={}, key_file=tmp_path / "a" / "fernet.key")
    second = mod.resolve(environ={}, key_file=tmp_path / "b" / "fernet.key")

    assert first != second


def test_the_helper_parses_on_the_runners_system_python():
    # The callers run it with the runner's `python3` (no setup-python step) —
    # 3.12 on ubuntu-latest — never with the backend's 3.14 venv this test runs
    # in. PEP 758's unparenthesised `except A, B:` (which `ruff format` produces
    # for a 3.14 target) is a SyntaxError there (security review of #1838, W-1).
    ast.parse(_SCRIPT.read_text(encoding="utf-8"), feature_version=(3, 10))


def test_a_symlinked_key_file_is_refused_not_followed(tmp_path: Path):
    mod = _module()
    victim = tmp_path / "victim.txt"
    victim.write_text("keep me\n")
    secrets_dir = tmp_path / ".e2e-secrets"
    secrets_dir.mkdir(mode=0o700)
    (secrets_dir / "fernet.key").symlink_to(victim)

    with pytest.raises(SystemExit):
        mod.resolve(environ={}, key_file=secrets_dir / "fernet.key")
    assert victim.read_text() == "keep me\n"


def test_a_corrupt_stored_key_is_refused_loudly_not_rotated(tmp_path: Path):
    # A silent rotation under a running stack leaves data it cannot decrypt.
    mod = _module()
    key_file = tmp_path / ".e2e-secrets" / "fernet.key"
    key_file.parent.mkdir(mode=0o700)
    key_file.write_text("garbage\n")

    with pytest.raises(SystemExit):
        mod.resolve(environ={}, key_file=key_file)
    assert key_file.read_text() == "garbage\n"


def test_an_exported_key_that_differs_from_the_stored_one_is_warned_about(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    mod = _module()
    key_file = tmp_path / ".e2e-secrets" / "fernet.key"
    mod.resolve(environ={}, key_file=key_file)
    other = Fernet.generate_key().decode()

    assert mod.resolve(environ={"E2E_FERNET_KEY": other}, key_file=key_file) == other
    assert "differs" in capsys.readouterr().err


def _reach_common():  # noqa: ANN202
    path = _SCRIPT.parent / "reach" / "_reach_common.py"
    spec = importlib.util.spec_from_file_location("_reach_common_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reach_teardown_does_not_need_the_key(monkeypatch: pytest.MonkeyPatch):
    # /code-review of #1861: a broken key file must not block `reach:stack:down` —
    # the helper's own advice is to remove the file *with the stack down*.
    reach = _reach_common()
    seen: list[dict[str, str]] = []

    def broken_key() -> str:
        raise reach.ReachError("key file is corrupt")

    def fake_run(command, **kwargs):  # noqa: ANN001, ANN202
        seen.append(kwargs["env"])
        return __import__("subprocess").CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(reach, "e2e_fernet_key", broken_key)
    monkeypatch.setattr(reach.subprocess, "run", fake_run)

    reach.run(reach.compose_command("down", "-v"), timeout=5)

    assert seen and "E2E_FERNET_KEY" not in seen[0]


def test_a_broken_key_file_surfaces_as_a_reach_error(monkeypatch: pytest.MonkeyPatch):
    reach = _reach_common()

    def refusing_helper(*_a, **_k):  # noqa: ANN002, ANN003, ANN202
        raise SystemExit("does not hold a Fernet key")

    monkeypatch.setattr(reach, "_load_key_helper", lambda: type("M", (), {"resolve": staticmethod(refusing_helper)}))

    with pytest.raises(reach.ReachError):
        reach.e2e_fernet_key()
