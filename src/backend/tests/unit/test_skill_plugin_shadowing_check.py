"""Tests for the plugin-shadowing guard (``scripts/check_skill_plugin_shadowing.py``).

**What is under test.** The detection logic, driven against *constructed* trees in
``tmp_path`` — never against the real ``.claude/`` or the real ``claude-shared``
checkout. A test asserting "this repository has two exemptions today" would go
red on the next legitimate adoption and teach nobody anything.

**The token-set rung is the point.** #1405's own pair —
``check-test-pyramid`` over ``nolte-engineering:test-pyramid-check`` — shares no
*name* with its pendant, only the same hyphen tokens in another order. An
exact-name guard, which is the obvious one to write, reports green on it.
:class:`TestItCanFail` pins that specific shape, so a future simplification of
``token_key`` back to string equality goes red here rather than silently
restoring the blind spot.

**The negative half matters as much.** :class:`TestItStaysGreen` pins that a
domain-only asset and a merely-overlapping name are *not* findings — a check that
flags everything is discarded, and then nothing is checked at all.

**The snapshot cannot rot.** The guard runs in CI from a names-only snapshot
because the runner has no plugin checkout. :class:`TestSnapshotIntegrity` pins
that a snapshot diverging from a reachable checkout is itself a finding, and that
an absent checkout is announced rather than silently skipped.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check and the
script lives outside the backend package, so it is loaded by path — the same
placement as the other source-tree gates. It is not a backend test in subject; it
is one in placement, because this is the tier that runs.

Traces to #1405 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from tests.support.repo_scripts import load_repo_script

checker = load_repo_script("check_skill_plugin_shadowing")


@pytest.fixture
def make_repo(tmp_path: Path) -> Callable[..., Path]:
    """Return a helper writing a fake repository root with ``.claude/`` assets."""

    def _make(
        *,
        skills: tuple[str, ...] = (),
        agents: tuple[str, ...] = (),
        document: dict | None = None,
    ) -> Path:
        root = tmp_path / "repo"
        for name in skills:
            skill_dir = root / ".claude" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
        agents_dir = root / ".claude" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        for name in agents:
            (agents_dir / f"{name}.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
        (root / ".claude" / "plugin-adoption.yml").write_text(
            yaml.safe_dump(document or {}), encoding="utf-8"
        )
        return root

    return _make


@pytest.fixture
def make_checkout(tmp_path: Path) -> Callable[..., Path]:
    """Return a helper writing a fake ``claude-shared`` checkout."""

    def _make(
        *,
        hub_skills: tuple[str, ...] = (),
        hub_agents: tuple[str, ...] = (),
        plugin_skills: dict[str, tuple[str, ...]] | None = None,
        plugin_agents: dict[str, tuple[str, ...]] | None = None,
        version: str = "0.0.1",
    ) -> Path:
        checkout = tmp_path / "claude-shared"
        manifest_dir = checkout / ".claude-plugin"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        (manifest_dir / "marketplace.json").write_text(
            json.dumps({"metadata": {"version": version}}), encoding="utf-8"
        )
        for name in hub_skills:
            skill_dir = checkout / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text("---\n---\n", encoding="utf-8")
        for name in hub_agents:
            agents = checkout / "agents"
            agents.mkdir(parents=True, exist_ok=True)
            (agents / f"{name}.md").write_text("---\n---\n", encoding="utf-8")
        for plugin, names in (plugin_skills or {}).items():
            for name in names:
                skill_dir = checkout / "plugins" / plugin / "skills" / name
                skill_dir.mkdir(parents=True, exist_ok=True)
                (skill_dir / "SKILL.md").write_text("---\n---\n", encoding="utf-8")
        for plugin, names in (plugin_agents or {}).items():
            agents = checkout / "plugins" / plugin / "agents"
            agents.mkdir(parents=True, exist_ok=True)
            for name in names:
                (agents / f"{name}.md").write_text("---\n---\n", encoding="utf-8")
        return checkout

    return _make


@pytest.fixture
def snapshot_of() -> Callable[..., dict]:
    """Return a helper rendering the snapshot document for a plugin inventory."""

    def _snapshot(
        *,
        plugin_skills: dict[str, tuple[str, ...]] | None = None,
        plugin_agents: dict[str, tuple[str, ...]] | None = None,
    ) -> dict:
        inventory: dict[str, dict[str, list[str]]] = {}
        for plugin, names in (plugin_skills or {}).items():
            inventory.setdefault(plugin, {"skills": [], "agents": []})["skills"] = list(names)
        for plugin, names in (plugin_agents or {}).items():
            inventory.setdefault(plugin, {"skills": [], "agents": []})["agents"] = list(names)
        return {"marketplace_version": "0.0.1", "inventory": inventory}

    return _snapshot


@pytest.fixture
def no_checkout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Point the checkout lookup at a path that does not exist."""
    monkeypatch.setenv(checker.ENV_VAR, str(tmp_path / "absent"))


class TestTokenKey:
    """The multiset key is what lifts the check above exact-name comparison."""

    def test_reordered_tokens_share_a_key(self) -> None:
        assert checker.token_key("check-test-pyramid") == checker.token_key("test-pyramid-check")

    def test_a_repeated_token_is_not_collapsed(self) -> None:
        # A set would equate these two; a capability named `a-b-b` is not `a-b`.
        assert checker.token_key("audit-test-test") != checker.token_key("audit-test")

    def test_different_tokens_do_not_share_a_key(self) -> None:
        assert checker.token_key("pre-pr") != checker.token_key("quality-gate")


class TestItCanFail:
    """Each finding shape, written deliberately and asserted red."""

    def test_reordered_name_is_a_finding(
        self, make_repo, make_checkout, monkeypatch, capsys
    ) -> None:
        """#1405's own shape: an exact-name guard would report green here."""
        repo = make_repo(skills=("check-test-pyramid",))
        checkout = make_checkout(plugin_skills={"nolte-engineering": ("test-pyramid-check",)})
        monkeypatch.setenv(checker.ENV_VAR, str(checkout))
        monkeypatch.setattr(
            checker, "load_adoption", lambda _p: {"inventory": {}, "allowlist": []}, raising=True
        )
        # The snapshot is empty on purpose here, so the drift finding fires too;
        # assert on the shadow line specifically.
        assert checker.run(repo) == 1
        err = capsys.readouterr().err
        assert "check-test-pyramid shadows nolte-engineering:test-pyramid-check" in err
        assert "token-set" in err

    def test_exact_name_is_a_finding(self, make_repo, make_checkout, monkeypatch, capsys) -> None:
        agents = {"nolte-engineering": ("fullstack-developer",)}
        repo = make_repo(
            agents=("fullstack-developer",),
            document={
                "inventory": {"nolte-engineering": {"skills": [], "agents": ["fullstack-developer"]}}
            },
        )
        monkeypatch.setenv(checker.ENV_VAR, str(make_checkout(plugin_agents=agents)))
        assert checker.run(repo) == 1
        err = capsys.readouterr().err
        assert "fullstack-developer shadows nolte-engineering:fullstack-developer" in err
        assert "exact" in err

    def test_stale_allowlist_entry_is_a_finding(
        self, make_repo, make_checkout, snapshot_of, monkeypatch, capsys
    ) -> None:
        """An exemption whose cause is gone is itself the finding."""
        document = snapshot_of(plugin_skills={"nolte-engineering": ("quality-gate",)})
        document["allowlist"] = [{"local": "deploy-ha", "reason": "domain-specific"}]
        repo = make_repo(skills=("deploy-ha",), document=document)
        monkeypatch.setenv(
            checker.ENV_VAR,
            str(make_checkout(plugin_skills={"nolte-engineering": ("quality-gate",)})),
        )
        assert checker.run(repo) == 1
        assert "no longer collides" in capsys.readouterr().err

    def test_allowlist_entry_without_a_reason_is_a_finding(
        self, make_repo, make_checkout, snapshot_of, monkeypatch, capsys
    ) -> None:
        document = snapshot_of(plugin_agents={"nolte-engineering": ("fullstack-developer",)})
        document["allowlist"] = [{"local": "fullstack-developer", "reason": "  "}]
        repo = make_repo(agents=("fullstack-developer",), document=document)
        monkeypatch.setenv(
            checker.ENV_VAR,
            str(make_checkout(plugin_agents={"nolte-engineering": ("fullstack-developer",)})),
        )
        assert checker.run(repo) == 1
        assert "with no reason" in capsys.readouterr().err


class TestItStaysGreen:
    """The negative half: what must not be flagged."""

    def test_domain_asset_is_not_a_finding(
        self, make_repo, make_checkout, snapshot_of, monkeypatch
    ) -> None:
        document = snapshot_of(plugin_skills={"nolte-engineering": ("quality-gate",)})
        repo = make_repo(skills=("plant-lifecycle", "deploy-ha"), document=document)
        monkeypatch.setenv(
            checker.ENV_VAR,
            str(make_checkout(plugin_skills={"nolte-engineering": ("quality-gate",)})),
        )
        assert checker.run(repo) == 0

    def test_partial_token_overlap_is_not_a_finding(
        self, make_repo, make_checkout, snapshot_of, monkeypatch
    ) -> None:
        """`check-seed-data` and `dependency-audit` share a shape, not a capability."""
        document = snapshot_of(plugin_skills={"nolte-engineering": ("guard-coverage-check",)})
        repo = make_repo(skills=("check-seed-data",), document=document)
        monkeypatch.setenv(
            checker.ENV_VAR,
            str(make_checkout(plugin_skills={"nolte-engineering": ("guard-coverage-check",)})),
        )
        assert checker.run(repo) == 0

    def test_reasoned_exemption_suppresses_its_own_finding_only(
        self, make_repo, make_checkout, snapshot_of, monkeypatch, capsys
    ) -> None:
        inventory = {"nolte-engineering": ("fullstack-developer", "quality-gate")}
        document = snapshot_of(plugin_agents={"nolte-engineering": ("fullstack-developer",)})
        document["inventory"]["nolte-engineering"]["skills"] = ["quality-gate"]
        document["allowlist"] = [{"local": "fullstack-developer", "reason": "parity not yet run"}]
        repo = make_repo(
            agents=("fullstack-developer",), skills=("quality-gate",), document=document
        )
        monkeypatch.setenv(
            checker.ENV_VAR,
            str(
                make_checkout(
                    plugin_agents={"nolte-engineering": ("fullstack-developer",)},
                    plugin_skills={"nolte-engineering": ("quality-gate",)},
                )
            ),
        )
        assert checker.run(repo) == 1
        err = capsys.readouterr().err
        assert "skills/quality-gate shadows" in err
        assert "agents/fullstack-developer shadows" not in err
        assert inventory  # the fixture data above is what the assertions describe


class TestSnapshotIntegrity:
    """The names-only snapshot is what makes the check runnable in CI."""

    def test_divergence_from_a_reachable_checkout_is_a_finding(
        self, make_repo, make_checkout, snapshot_of, monkeypatch, capsys
    ) -> None:
        document = snapshot_of(plugin_skills={"nolte-engineering": ("quality-gate",)})
        repo = make_repo(skills=("plant-lifecycle",), document=document)
        monkeypatch.setenv(
            checker.ENV_VAR,
            str(
                make_checkout(
                    plugin_skills={"nolte-engineering": ("quality-gate", "dependency-audit")}
                )
            ),
        )
        assert checker.run(repo) == 1
        err = capsys.readouterr().err
        assert "has drifted from" in err
        assert "nolte-engineering:dependency-audit" in err

    def test_absent_checkout_runs_the_check_and_says_so(
        self, make_repo, snapshot_of, no_checkout, capsys
    ) -> None:
        """The CI shape: no checkout, a loud note, and the shadow check still runs."""
        document = snapshot_of(plugin_skills={"nolte-engineering": ("test-pyramid-check",)})
        repo = make_repo(skills=("check-test-pyramid",), document=document)
        assert checker.run(repo) == 1
        captured = capsys.readouterr()
        assert "no claude-shared checkout found" in captured.err
        assert "check-test-pyramid shadows" in captured.err

    def test_absent_checkout_and_empty_snapshot_is_a_usage_error(
        self, make_repo, no_checkout, capsys
    ) -> None:
        """Never green on nothing: a check with no inventory examines nothing."""
        repo = make_repo(skills=("plant-lifecycle",), document={})
        assert checker.run(repo) == 2
        assert "would examine nothing" in capsys.readouterr().err

    def test_refresh_rewrites_the_snapshot_from_the_checkout(
        self, make_repo, make_checkout, snapshot_of, monkeypatch
    ) -> None:
        document = snapshot_of(plugin_skills={"nolte-engineering": ("quality-gate",)})
        document["allowlist"] = [{"local": "plant-lifecycle", "reason": "kept for this test"}]
        repo = make_repo(skills=("plant-lifecycle",), document=document)
        monkeypatch.setenv(
            checker.ENV_VAR,
            str(
                make_checkout(
                    plugin_skills={"nolte-engineering": ("quality-gate", "dependency-audit")},
                    version="9.9.9",
                )
            ),
        )
        assert checker.run(repo, refresh=True) == 0
        written = yaml.safe_load((repo / ".claude" / "plugin-adoption.yml").read_text())
        assert written["marketplace_version"] == "9.9.9"
        assert written["inventory"]["nolte-engineering"]["skills"] == [
            "dependency-audit",
            "quality-gate",
        ]
        # The allowlist is the human half of the file and survives a refresh.
        assert written["allowlist"][0]["local"] == "plant-lifecycle"
