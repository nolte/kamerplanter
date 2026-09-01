"""Tests for the notification-write counter (``scripts/check_notification_write_boundary.py``).

**What is under test.** The detection logic against **constructed** trees in
``tmp_path``, plus one ratchet that reads the real tree through a named register
rather than a number — the same split as
``test_recurrence_boundary_check.py``, and for the same reason.

**The receiver-resolution test is the one that matters.** ``self._repo`` is a
notification repository in ``notification_propagation_service.py`` and a *task*
repository in ``task_service.py``. A checker that matched on the attribute name
would flag every task write in the codebase and be switched off inside a day; one
that matched only on ``notification`` in the name would miss the owner's own
calls. Both directions are pinned below.

**Red first, and the falsification asserts the same expression.** Each "it stays
quiet" test has a partner showing the same construct going red when the one thing
that excuses it is removed.

Traces to ADR-008 phase 0 and issue #1061, feature F-6 (no TC-ID: a source-tree
gate is not a user-facing case).
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from tests.support.repo_scripts import find_repo_root, load_repo_script

checker = load_repo_script("check_notification_write_boundary")


def scan(source: str, name: str = "some_service.py") -> list:
    """Scan one module's source text as if it were a file called *name*."""
    return checker.scan_source(Path(name), textwrap.dedent(source))


_NAMED_RECEIVER = """
class Sender:
    def __init__(self, notification_repo):
        self._notification_repo = notification_repo

    def announce(self, notification):
        return self._notification_repo.create(notification)
"""

_ANNOTATED_RECEIVER = """
from app.domain.interfaces.notification_repository import INotificationRepository


class Follower:
    def __init__(self, repo: INotificationRepository) -> None:
        self._repo = repo

    def follow(self, notification):
        return self._repo.update(notification.key, notification)
"""

_TASK_REPOSITORY_LOOKALIKE = """
from app.domain.interfaces.task_repository import ITaskRepository


class TaskService:
    def __init__(self, repo: ITaskRepository) -> None:
        self._repo = repo

    def complete(self, key, task):
        return self._repo.update(key, task)
"""


# ── It can fail ──────────────────────────────────────────────────────────────


class TestItCanFail:
    """A gate nobody has watched fail is a gate nobody knows works."""

    def test_a_named_notification_repository_write_is_reported(self) -> None:
        sites = scan(_NAMED_RECEIVER)
        assert len(sites) == 1
        assert sites[0].kind == "notification_write"
        assert (sites[0].receiver, sites[0].method) == ("self._notification_repo", "create")
        assert sites[0].function == "announce"
        assert not sites[0].justified

    def test_an_annotated_receiver_is_resolved_even_when_its_name_says_nothing(self) -> None:
        """``self._repo`` gives the checker no vocabulary; the annotation does."""
        sites = scan(_ANNOTATED_RECEIVER)
        assert len(sites) == 1
        assert (sites[0].receiver, sites[0].method) == ("self._repo", "update")

    def test_every_mutating_method_of_the_interface_is_watched(self) -> None:
        sites = scan(
            """
            class Sender:
                def __init__(self, notification_repo):
                    self._notification_repo = notification_repo

                def churn(self, n, now):
                    self._notification_repo.create(n)
                    self._notification_repo.update(n.key, n)
                    self._notification_repo.delete(n.key)
                    self._notification_repo.mark_read(n.key, now)
                    self._notification_repo.mark_acted(n.key, now)
            """
        )
        assert {site.method for site in sites} == set(checker.MUTATING_METHODS)

    def test_a_factory_bound_local_is_resolved(self) -> None:
        sites = scan(
            """
            def announce(notification):
                repo = get_notification_repo()
                return repo.create(notification)
            """
        )
        assert [site.method for site in sites] == ["create"]


# ── What it must refuse to report ────────────────────────────────────────────


class TestTheQuietSide:
    """A checker that flags every ``self._repo.update`` guards nothing at all."""

    def test_a_task_repository_with_the_same_attribute_name_is_not_a_notification_write(self) -> None:
        """The whole reason receiver resolution is annotation-first, not name-first."""
        assert scan(_TASK_REPOSITORY_LOOKALIKE) == []

    def test_the_same_module_flags_the_notification_repository_next_to_it(self) -> None:
        """The negative control: one module, two ``self._…`` repositories, one finding.

        Without this the test above proves only that *something* was quiet — it
        would pass just as well if the checker were inert.
        """
        sites = scan(
            _TASK_REPOSITORY_LOOKALIKE
            + """

class Sender:
    def __init__(self, notification_repo):
        self._notification_repo = notification_repo

    def announce(self, notification):
        return self._notification_repo.create(notification)
"""
        )
        assert [(site.receiver, site.method) for site in sites] == [("self._notification_repo", "create")]

    def test_reads_are_not_writes(self) -> None:
        sites = scan(
            """
            class Reader:
                def __init__(self, notification_repo):
                    self._notification_repo = notification_repo

                def show(self, user_key, tenant_key):
                    self._notification_repo.list_for_user(user_key, tenant_key)
                    self._notification_repo.count_unread(user_key, tenant_key)
                    return self._notification_repo.get("k")
            """
        )
        assert sites == []

    def test_constructing_a_notification_is_not_writing_one(self) -> None:
        """``ha_notification_channel`` builds one and persists nothing — a blind spot, pinned."""
        sites = scan(
            """
            from app.domain.models.notification import Notification

            def to_notification(payload):
                return Notification(title=payload["title"], body=payload["body"])
            """
        )
        assert sites == []


# ── The write-class declaration, and its negative control ────────────────────


_DECLARED_EVENT = """
class Engine:
    def __init__(self, notification_repo):
        self._notification_repo = notification_repo

    def notify(self, notification):
        # notification-write-ok: event: the first materialisation of an inbound event
        return self._notification_repo.create(notification)
"""


class TestTheWriteClassDeclaration:
    """Only the two classes ADR-008 names outside the boundary are accepted."""

    def test_an_event_declaration_excuses_the_write(self) -> None:
        sites = scan(_DECLARED_EVENT)
        assert len(sites) == 1
        assert sites[0].justified
        assert sites[0].write_class == "event"

    def test_a_user_action_declaration_excuses_the_write(self) -> None:
        sites = scan(
            """
            class Service:
                def __init__(self, notification_repo):
                    self._notification_repo = notification_repo

                def mark_read(self, key, now):
                    # notification-write-ok: user-action: the reader marked their own row read
                    return self._notification_repo.mark_read(key, now)
            """
        )
        assert sites[0].justified and sites[0].write_class == "user-action"

    def test_removing_the_declaration_makes_the_same_site_red_again(self) -> None:
        """The negative control, on the same expression the positive test used."""
        without = _DECLARED_EVENT.replace(
            "        # notification-write-ok: event: the first materialisation of an inbound event\n", ""
        )
        assert without != _DECLARED_EVENT
        sites = scan(without)
        assert len(sites) == 1 and not sites[0].justified

    def test_an_unknown_class_is_not_an_exemption(self) -> None:
        """`propagation` is not a third option — it is the owner's, by definition."""
        sites = scan(
            _DECLARED_EVENT.replace(
                "event: the first materialisation of an inbound event",
                "propagation: the task moved so its notification follows",
            )
        )
        assert len(sites) == 1
        assert sites[0].kind == "unknown_write_class"
        assert sites[0].write_class == "propagation"
        assert not sites[0].justified

    def test_a_class_without_a_reason_is_not_an_exemption(self) -> None:
        sites = scan(_DECLARED_EVENT.replace("event: the first materialisation of an inbound event", "event: no"))
        assert len(sites) == 1 and not sites[0].justified

    def test_a_reason_without_a_class_is_not_an_exemption(self) -> None:
        """The class is the point: an unclassified write is exactly what phase 2 counts."""
        sites = scan(
            _DECLARED_EVENT.replace(
                "event: the first materialisation of an inbound event",
                "the first materialisation of an inbound event",
            )
        )
        assert len(sites) == 1 and not sites[0].justified


class TestTheRegisterCannotOutliveItsDebt:
    """A declaration left behind after the write moved declares nothing, and must go."""

    def test_a_declaration_with_no_write_under_it_is_a_finding(self) -> None:
        sites = scan(
            """
            class Engine:
                def __init__(self, notification_repo):
                    self._notification_repo = notification_repo

                def notify(self, notification):
                    # notification-write-ok: event: this used to create a row, and does not any more
                    return None
            """
        )
        assert len(sites) == 1
        assert sites[0].kind == "stale_justification"
        assert not sites[0].justified

    def test_a_declaration_that_still_covers_a_write_is_not_stale(self) -> None:
        """The negative control: the same marker, with the call still under it."""
        assert [site.kind for site in scan(_DECLARED_EVENT)] == ["notification_write"]


# ── The tree contract ────────────────────────────────────────────────────────


class TestTheTreeContract:
    """Discovery, owner exclusion, exit codes and the machine-readable shape."""

    def _tree(self, root: Path, files: dict[str, str]) -> Path:
        for relative, source in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(textwrap.dedent(source), encoding="utf-8")
        return root

    def test_the_owner_and_the_repository_definition_are_not_counted(self, tmp_path: Path) -> None:
        root = self._tree(
            tmp_path,
            {
                "domain/services/notification_propagation_service.py": _NAMED_RECEIVER,
                "data_access/arango/notification_repository.py": _NAMED_RECEIVER,
                "domain/interfaces/notification_repository.py": _NAMED_RECEIVER,
                "domain/services/other_service.py": _NAMED_RECEIVER,
            },
        )
        sites = checker.collect(root)
        assert [site.relative().endswith("other_service.py") for site in sites] == [True]

    def test_an_empty_scan_root_is_a_usage_error_not_a_green(self, tmp_path: Path) -> None:
        (tmp_path / "empty").mkdir()
        assert checker.main(["--scan-root", str(tmp_path / "empty")]) == checker.EXIT_USAGE

    def test_gate_mode_is_red_and_inventory_mode_is_not(self, tmp_path: Path) -> None:
        root = self._tree(tmp_path, {"service.py": _NAMED_RECEIVER})
        assert checker.main(["--scan-root", str(root)]) == checker.EXIT_DEFECTS
        assert checker.main(["--scan-root", str(root), "--inventory"]) == checker.EXIT_OK

    def test_json_reports_counts_classes_and_site_attribution(self, tmp_path: Path, capsys) -> None:  # noqa: ANN001
        root = self._tree(tmp_path, {"a.py": _DECLARED_EVENT, "b.py": _NAMED_RECEIVER})
        assert checker.main(["--scan-root", str(root), "--json"]) == checker.EXIT_DEFECTS
        payload = json.loads(capsys.readouterr().out)
        assert (payload["total"], payload["open"], payload["justified"]) == (2, 1, 1)
        assert {site["write_class"] for site in payload["sites"]} == {"event", None}


# ── The ratchet, against the real tree ───────────────────────────────────────


#: Every notification write the backend still makes outside
#: ``NotificationPropagationService`` **without** declaring its write class.
#:
#: **This is the phase-0 (b) baseline of ADR-008**, and it is short — which is
#: the finding, not an oversight. Six of the seven writes outside the owner are
#: event materialisation (``NotificationEngine``) or a user acting on their own
#: row (``NotificationService``), both named outside the boundary by the phase-0
#: counting definition; they carry their declaration at the site.
#:
#: **What this register does NOT measure, and phase 2 must:** the propagation
#: that never happens. This counts writes made in the wrong place; the #742/#769
#: class is a source mutation with *no* notification call at all, which no
#: scanner of this shape can see. See
#: ``.audits/adr-008-phase-0-inventory/2026-09-01-inventory.md`` §"Was der Scan
#: nicht sieht" for the hand-found candidates.
#:
#: Same two ratchet properties as the recurrence register, and the same
#: departure from NFR-018 §2.1 for the same reason (a per-site register has no
#: shared line to collide on, and it cannot go quietly stale).
_KNOWN_OPEN: dict[str, tuple[int, str]] = {
    "src/backend/app/domain/engines/notification_engine.py::escalate_overdue::self._notification_repo.update": (
        1,
        "The overdue-watering escalation stamps `escalation_level` back onto the *existing* "
        "care notification — a row NotificationPropagationService also owns and writes via the "
        "same care `group_key`. Two writers on one row is the #548 shape, and the reason this "
        "one is debt rather than an `event` declaration: the row is not being born here, it is "
        "being followed. Phase 2 moves it behind the propagation service.",
    ),
}


def _real_tree_sites() -> list:
    root = find_repo_root(Path(__file__).resolve())
    if root is None:  # pragma: no cover — only outside a full checkout
        pytest.skip("checkout root not found")
    return [site for site in checker.collect(root / checker.DEFAULT_SCAN_ROOT) if not site.justified]


class TestTheRatchet:
    """The ADR-008 phase-0 (b) baseline, as a register that must shrink to nothing."""

    def test_no_notification_write_arrives_outside_the_register(self) -> None:
        counted: dict[str, int] = {}
        for site in _real_tree_sites():
            counted[site.identity()] = counted.get(site.identity(), 0) + 1

        arrived = {
            identity: count for identity, count in counted.items() if count > _KNOWN_OPEN.get(identity, (0, ""))[0]
        }
        assert not arrived, (
            "New notification write(s) outside NotificationPropagationService (ADR-008 "
            "boundary 3): "
            + "; ".join(f"{identity} (now {count})" for identity, count in sorted(arrived.items()))
            + ". Route the write through the propagation service, or declare its class at the "
            "site ('# notification-write-ok: event|user-action: <reason>'). Run "
            "`task check:notification-write-boundary -- --inventory` to see the full picture."
        )

    def test_a_healed_entry_must_leave_the_register(self) -> None:
        counted: dict[str, int] = {}
        for site in _real_tree_sites():
            counted[site.identity()] = counted.get(site.identity(), 0) + 1

        healed = {
            identity: (registered, counted.get(identity, 0))
            for identity, (registered, _) in _KNOWN_OPEN.items()
            if counted.get(identity, 0) < registered
        }
        assert not healed, (
            "These entries no longer describe the tree and must be removed from _KNOWN_OPEN "
            "(or their count lowered): "
            + "; ".join(
                f"{identity} (registered {was}, found {now})" for identity, (was, now) in sorted(healed.items())
            )
            + ". A register that outlives its debt stops being evidence of anything."
        )

    def test_the_register_retires_itself_when_the_debt_is_gone(self) -> None:
        """The obsolescence rule ADR-008 phase 2 exits on.

        Reaching zero here is **not** the same as "every edge is wired" — see the
        register's note. It means no caller reaches around the owner; the missing
        edges are F-8's pairing tests to prove, not this counter's.
        """
        assert _KNOWN_OPEN, (
            "The phase-0 (b) baseline is empty: no undeclared notification write outside "
            "NotificationPropagationService remains. Delete this register and its two tests "
            "above, and wire scripts/check_notification_write_boundary.py into "
            ".pre-commit-config.yaml as a hook in the required `static` lane (ADR-008 phase 4 / "
            "feature F-10). Leaving an empty register in place would be a gate that can no "
            "longer fail — and remember it never covered the missing-edge half."
        )
