"""#1506 class sweep — a service that clears a field, against a repository that drops it.

``BaseArangoRepository._update_is_full_replace`` is ``False`` by default. In that
**merge** mode :meth:`_update_doc` dumps the model with ``exclude_none=True`` and
calls ``collection.update(..., keep_none=True)``, so a field the caller set to
``None`` never appears in the payload and the stored value survives an update that
meant to clear it. Nothing warns: the write returns 200 with the old value.

``care_profiles`` was the repository #1506 measured — ``reset_profile`` could not
drop the note it was replacing, ``DormancyCareActivator.deactivate`` could not drop
the winter watering regime — and it is now full-replace. The *class* is wider than
the one repository, so this guard exists to make every remaining instance a
deliberate, written-down decision rather than a discovery.

**What it measures.** Every function under :data:`_SCAN_ROOTS` —
``app/domain/services``, ``app/migrations/versions`` and ``app/tasks`` — that both

1. writes a ``None`` into something that looks like a persisted model — an
   attribute assignment ``obj.field = None``, a subscript ``data["field"] = None``,
   a ``model_copy(update={"field": None})`` or a ``Model(**{..., "field": None})``
   splat (a local variable bound to ``None`` counts as ``None``) — **and**
2. hands the result to a repository method named ``update`` / ``update_*`` on
   ``self`` (``update_fields`` and ``update_fields_checked`` excluded: those write
   ``keep_none=True`` and are the *supported* way to clear a field),

is a candidate, and every candidate must appear in :data:`_REVIEWED` with the
verdict it was measured to have. An unlisted candidate fails this test; so does a
listed one that has disappeared, because a stale entry is how an inventory starts
lying about what was checked.

**What it is not.** It cannot resolve ``self._repo`` to a concrete repository class
— services take their repositories through an interface — so it cannot decide the
verdict itself. The verdict is the measurement, recorded here; the guard's job is
to notice that a *new* one needs making.

**A spelling it does not match**, stated with its live example rather than
discovered later: the scan is **per function**, so a clear and the write that
carries it must sit in the same one. They do not in the v0050 repair migration —
``_merge`` nulls the two learned intervals, ``_process_batch`` calls
``update_profile`` — and that pair is precisely the write that *measured* the #1506
defect. It is in the scan's roots and still invisible to it. The same hole covers
any clear routed through a helper, a ``setattr(obj, name, None)``, and a ``None``
that only ever arrives as a parameter default.

``_REVIEWED`` is therefore a floor on the class, not a proof of its size. Two of
the entries below (``dormancy_care_activator.activate`` and
``care_reminder_service.confirm_reminder``) are visible at all only because the
scan resolves locals bound to ``None`` — the first draft missed ``activate``
entirely, which is what that resolution was added for.
"""

from __future__ import annotations

import ast
from importlib import import_module
from pathlib import Path

from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"

#: Where a field-clearing writer can live.
#:
#: ``domain/services`` is where the class was first measured; the other two were
#: added in the #1506 review (SCR-009) because both hold writers of exactly this
#: shape, and a scan that stopped at the services would have been complete-looking
#: and blind to them:
#:
#: * ``migrations/versions`` — v0050's ``_merge`` nulls the two learned intervals and
#:   hands the full model to ``update_profile``; it is the very write that measured
#:   the defect, and it was outside the first draft's reach.
#: * ``tasks`` — the Celery beat tasks (retention, care generation, actuator loop)
#:   drive services *and* repositories directly.
_SCAN_ROOTS = (
    _APP / "domain" / "services",
    _APP / "migrations" / "versions",
    _APP / "tasks",
)

#: Field-clearing writes reaching these are *not* dropped: they end in
#: ``_update_doc_fields``, which passes ``keep_none=True``.
_KEEP_NONE_METHODS = frozenset({"update_fields", "update_fields_checked"})

#: The measured inventory: ``module::function`` → the verdict, written out.
#:
#: ``REPAIRED (#NNNN)`` — the named change made the target repository full-replace,
#: so the clear lands. Every one of them is measured against a real ArangoDB in
#: ``tests/integration/test_merge_mode_null_clearing.py`` (or, for ``care_profiles``,
#: ``test_care_profile_null_clearing.py``), and
#: :class:`TestEveryRepairedSiteReachesAFullReplaceRepository` below re-derives the
#: flag from the code rather than trusting this string.
#: ``SAFE`` — the repository was already full-replace, the write path already keeps
#: nulls, or the ``None`` never reaches a stored field at all.
#: ``DEFECT #NNNN`` — measured to be dropped; tracked in its own issue, because
#: flipping a repository needs its own writer×fields table and red-first pass
#: (which is what #1506 was for ``care_profiles``), not a drive-by edit. No entry
#: carries this verdict today — #1525 and #1516 closed the last of them.
_REVIEWED: dict[str, str] = {
    # ── repaired by #1506 ────────────────────────────────────────────────────
    "care_reminder_service::update_profile": (
        "REPAIRED (#1506) — clears watering_interval_learned/fertilizing_interval_learned on an "
        "explicit interval edit (#622); ArangoCareReminderRepository is full-replace."
    ),
    "dormancy_care_activator::activate": (
        "REPAIRED (#1506) — an OverwinteringProfile without winter_watering clears a stale "
        "dormancy_watering; ArangoCareReminderRepository is full-replace."
    ),
    "dormancy_care_activator::deactivate": (
        "REPAIRED (#1506) — leaving dormancy clears dormancy_watering (REQ-047 §3.5)."
    ),
    # ── repositories that were already full-replace ──────────────────────────
    "plant_instance_service::remove_plant": (
        "SAFE — clears PlantInstance.cover_photo_ref; ArangoPlantInstanceRepository sets "
        "_update_is_full_replace (#714)."
    ),
    "planting_run_service::_reassign_plant_slots": (
        "SAFE — clears PlantInstance.slot_key ('not placed anywhere'), the case "
        "_update_is_full_replace was introduced for."
    ),
    # ── the None never reaches a stored field ────────────────────────────────
    "actuator_service::_dispatch": (
        "SAFE — `error_message` is a local carried into a freshly constructed ControlEvent that "
        "is inserted (create_event); the update on this path writes the actuator, not the event."
    ),
    "care_reminder_service::confirm_reminder": (
        "SAFE — `watering_log_key` is a local initialised to None and only ever written onto a "
        "newly created CareConfirmation."
    ),
    "favorites_service::_add_one": (
        "SAFE — the `cascade_from_key` clear is a raw driver write "
        "(`self._db.collection(...).update(...)`), and python-arango's `keep_none` default is "
        "True, so the null is stored. Not a BaseArangoRepository path at all."
    ),
    "import_service::confirm": (
        "SAFE — the name is `update_fn`, a local callable initialised to None; no model field."
    ),
    "plant_photo_service::assess_photo": (
        "SAFE — `expected_scientific_name` is a local passed to the assessment call, not a field "
        "of the model that is written."
    ),
    # ── repaired by #1525 / #1516 ────────────────────────────────────────────
    #
    # Each repository was its own measurement: flipping `_update_is_full_replace`
    # alters null semantics for every writer of that collection, so each carries a
    # writer×fields table on the flag itself (the shape #1506 used for
    # care_profiles) plus a red-first pass against a real ArangoDB in
    # `tests/integration/test_merge_mode_null_clearing.py`.
    "user_service::delete_account": (
        "REPAIRED (#1525) — the soft-delete nulls User.password_hash and avatar_url; "
        "ArangoUserRepository is full-replace, so the stored bcrypt hash is removed with the "
        "same write that sets is_active/email/display_name."
    ),
    "privacy_service::request_erasure": (
        "REPAIRED (#1525) — the same soft-delete on the DSGVO Art. 17 path; the credential no "
        "longer survives the 90 days until the hard delete runs."
    ),
    "privacy_service::grant_consent": (
        "REPAIRED (#1516) — re-granting a revoked consent clears revoked_at (and the previous "
        "grant's ip_address/user_agent when the new one supplies none); ArangoConsentRepository "
        "is full-replace."
    ),
    "task_service::reopen_task": (
        "REPAIRED (#1516) — a reopened task drops completed_at, actual_duration_minutes, "
        "completion_notes, difficulty_rating and quality_rating; ArangoTaskRepository is "
        "full-replace."
    ),
    "phase_service::delete_phase_history": (
        "REPAIRED (#1516) — reopening the previous phase clears exited_at/actual_duration_days; "
        "_PhaseHistoryRepository is full-replace. Its sibling clears on the PlantInstance "
        "(current_phase_key/_started_at) always landed — that repository was already "
        "full-replace — which is why the function looked half-correct."
    ),
    "phase_service::update_phase_history_dates": (
        "REPAIRED (#1516) — clears actual_duration_days when the exit date is removed; same repository."
    ),
    "planting_run_service::batch_update_phase_dates": ("REPAIRED (#1516) — the same clear on the batch path."),
    "onboarding_service::reset_wizard": (
        "REPAIRED (#1516) — the wizard reset clears completed_at, site_type, selected_site_key, "
        "selected_kit_id, selected_experience_level and plant_count; "
        "ArangoOnboardingStateRepository is full-replace."
    ),
    "onboarding_service::ensure_onboarding_state_for_user": (
        "REPAIRED (#1516) — clears completed_at on the same repository (REQ-027 takeover path)."
    ),
    "notification_propagation_service::_update_single": (
        "REPAIRED (#1516) — under `reset_read` it clears read_at/acted_at so the row re-surfaces "
        "in the badge (#769); ArangoNotificationRepository is full-replace."
    ),
}


#: ``module::function`` → the repository class the full-model write reaches, or
#: ``None`` when the ``None`` never reaches a stored field at all.
#:
#: This is what turns :data:`_REVIEWED` from prose into something checkable. The
#: scanner cannot resolve ``self._repo`` — the services take their repositories
#: through an interface — so the resolution is declared here *once*, by hand, and
#: :class:`TestEveryVerdictMatchesTheRepositoryItNames` then re-derives
#: ``_update_is_full_replace`` from the class instead of believing the sentence.
#:
#: The consequence that matters: a verdict and its repository cannot drift apart.
#: Marking a site ``REPAIRED`` without flipping the flag fails; flipping a flag
#: back to merge mode while a site still claims ``REPAIRED`` fails; leaving a site
#: at ``DEFECT`` after its repository became full-replace fails too — the direction
#: an inventory of "known problems" normally rots in.
_SITE_REPOSITORY: dict[str, str | None] = {
    "care_reminder_service::update_profile": "care_reminder_repository.ArangoCareReminderRepository",
    "dormancy_care_activator::activate": "care_reminder_repository.ArangoCareReminderRepository",
    "dormancy_care_activator::deactivate": "care_reminder_repository.ArangoCareReminderRepository",
    "plant_instance_service::remove_plant": "plant_instance_repository.ArangoPlantInstanceRepository",
    "planting_run_service::_reassign_plant_slots": "plant_instance_repository.ArangoPlantInstanceRepository",
    "actuator_service::_dispatch": None,
    "care_reminder_service::confirm_reminder": None,
    "favorites_service::_add_one": None,
    "import_service::confirm": None,
    "plant_photo_service::assess_photo": None,
    "user_service::delete_account": "user_repository.ArangoUserRepository",
    "privacy_service::request_erasure": "user_repository.ArangoUserRepository",
    "privacy_service::grant_consent": "consent_repository.ArangoConsentRepository",
    "task_service::reopen_task": "task_repository.ArangoTaskRepository",
    "phase_service::delete_phase_history": "lifecycle_repository._PhaseHistoryRepository",
    "phase_service::update_phase_history_dates": "lifecycle_repository._PhaseHistoryRepository",
    "planting_run_service::batch_update_phase_dates": "lifecycle_repository._PhaseHistoryRepository",
    "onboarding_service::reset_wizard": "onboarding_state_repository.ArangoOnboardingStateRepository",
    "onboarding_service::ensure_onboarding_state_for_user": (
        "onboarding_state_repository.ArangoOnboardingStateRepository"
    ),
    "notification_propagation_service::_update_single": "notification_repository.ArangoNotificationRepository",
}


def _is_full_replace(dotted: str) -> bool:
    """``_update_is_full_replace`` as the class actually declares it."""
    module_name, class_name = dotted.split(".")
    module = import_module(f"app.data_access.arango.{module_name}")
    return bool(getattr(module, class_name)._update_is_full_replace)


# ── the scanner ──────────────────────────────────────────────────────────────


def _names_bound_to_none(fn: ast.AST) -> set[str]:
    """Local names assigned a literal ``None`` somewhere in this function."""
    bound: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and node.value.value is None:
            bound |= {t.id for t in node.targets if isinstance(t, ast.Name)}
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.value, ast.Constant)
            and node.value.value is None
            and isinstance(node.target, ast.Name)
        ):
            bound.add(node.target.id)
    return bound


def _is_none(value: ast.AST, bound: set[str]) -> bool:
    return (isinstance(value, ast.Constant) and value.value is None) or (
        isinstance(value, ast.Name) and value.id in bound
    )


def _cleared_fields(fn: ast.AST) -> set[str]:
    """Field names this function writes as ``None`` into something model-shaped."""
    bound = _names_bound_to_none(fn)
    cleared: set[str] = set()
    for node in ast.walk(fn):
        # obj.field = None / data["field"] = None
        if isinstance(node, ast.Assign) and _is_none(node.value, bound):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and not (
                    isinstance(target.value, ast.Name) and target.value.id == "self"
                ):
                    cleared.add(target.attr)
                elif isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant):
                    cleared.add(str(target.slice.value))
        # Model(field=None) / model_copy(update={"field": None}) / Model(**{"field": None})
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg is not None and _is_none(keyword.value, bound):
                    cleared.add(keyword.arg)
                elif isinstance(keyword.value, ast.Dict):
                    cleared |= _none_keys(keyword.value, bound)
            for arg in node.args:
                if isinstance(arg, ast.Dict):
                    cleared |= _none_keys(arg, bound)
    return cleared


def _none_keys(node: ast.Dict, bound: set[str]) -> set[str]:
    return {
        str(key.value)
        for key, value in zip(node.keys, node.values, strict=False)
        if isinstance(key, ast.Constant) and _is_none(value, bound)
    }


def _full_model_update_calls(fn: ast.AST) -> set[str]:
    """Repository ``update``/``update_*`` calls on ``self`` that rewrite a full model."""
    calls: set[str] = set()
    for node in ast.walk(fn):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        name = node.func.attr
        if not (name == "update" or name.startswith("update_")) or name in _KEEP_NONE_METHODS:
            continue
        # Anchored on ``self.<collaborator>`` so ``some_dict.update(...)`` — the
        # spelling that shares the method name and means something else entirely —
        # is not read as a repository write. The chain is unwound through
        # intermediate **calls** as well, because ``self._require_prop().update_*``
        # is an ordinary spelling here and an attribute-only unwind lost it.
        receiver: ast.AST = node.func.value
        while isinstance(receiver, ast.Attribute | ast.Call):
            receiver = receiver.value if isinstance(receiver, ast.Attribute) else receiver.func
        if isinstance(receiver, ast.Name) and receiver.id == "self":
            calls.add(name)
    return calls


def _measured() -> dict[str, set[str]]:
    """``module::function`` → the fields it clears, for every candidate."""
    found: dict[str, set[str]] = {}
    for path in sorted(p for root in _SCAN_ROOTS for p in root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            cleared = _cleared_fields(node)
            if cleared and _full_model_update_calls(node):
                found[f"{path.stem}::{node.name}"] = cleared
    return found


# ── the guard ────────────────────────────────────────────────────────────────


class TestEveryFieldClearingWriterHasBeenMeasured:
    def test_no_unreviewed_writer_appeared(self):
        """A new clear-then-update site must be measured before it is merged.

        Fails with the site and the fields it clears; the fix is to determine which
        repository the write reaches and record the verdict in ``_REVIEWED`` — not
        to add the name.
        """
        measured = _measured()
        unreviewed = {site: sorted(fields) for site, fields in measured.items() if site not in _REVIEWED}

        assert unreviewed == {}, (
            "these service functions clear a field and then write a full model through a "
            "repository update; measure whether that repository merges (the value survives) "
            "or full-replaces, and record the verdict in _REVIEWED:\n"
            + "\n".join(f"  {site}: {fields}" for site, fields in sorted(unreviewed.items()))
        )

    def test_no_entry_outlived_the_code_it_describes(self):
        """A verdict about a function that no longer clears anything is not evidence.

        This is the half that keeps the inventory from turning into a list of
        reassurances nobody re-derived: a rename or a refactor drops the site out of
        the scan, and the stale entry has to go with it.
        """
        measured = _measured()
        stale = sorted(site for site in _REVIEWED if site not in measured)

        assert stale == [], (
            "_REVIEWED describes sites the scan no longer finds; remove them (or restore the "
            f"scan's reach if they were renamed): {stale}"
        )


class TestTheScanStillSeesTheDefectItWasWrittenFor:
    """Falsification: the scanner must match the #1506 sites themselves.

    Without this, a scanner that matched nothing at all would pass both assertions
    above the moment ``_REVIEWED`` were emptied — the vacuous-guard shape this
    repository keeps paying for.
    """

    def test_the_two_repaired_care_sites_are_matched(self):
        measured = _measured()

        assert "dormancy_care_activator::deactivate" in measured
        assert "dormancy_watering" in measured["dormancy_care_activator::deactivate"]
        assert "dormancy_care_activator::activate" in measured, (
            "the scan lost the local-bound-to-None resolution; `watering = None` is how the "
            "activate path spells the same clear"
        )

    def test_a_keep_none_write_path_is_not_the_reason_a_site_matches(self):
        """``update_fields`` is the supported clear, so it must not count as a hit.

        ``plant_diary_service`` reaches the scan through other ``update`` calls in the
        same functions; what this pins is that the *method name* alone does not.
        """
        source = ast.parse(
            "def f():\n    entry.analysis_error = None\n    self._repo.update_fields(key, {'analysis_error': None})\n"
        )
        fn = source.body[0]

        assert _cleared_fields(fn) == {"analysis_error"}
        assert _full_model_update_calls(fn) == set()


class TestEveryVerdictMatchesTheRepositoryItNames:
    """The inventory's verdicts, re-derived from the repository classes themselves.

    ``_REVIEWED`` is a wall of sentences, and a sentence keeps reading correctly
    long after the code under it has moved — the failure this repository keeps
    paying for. Each verdict names a consequence that is decided by exactly one
    machine-readable fact, ``_update_is_full_replace`` on the repository the write
    reaches, so that fact is read off the class here rather than believed.
    """

    def test_every_reviewed_site_declares_the_repository_it_writes_to(self):
        """A new verdict has to name its repository, not just assert a conclusion."""
        missing = sorted(set(_REVIEWED) - set(_SITE_REPOSITORY))
        extra = sorted(set(_SITE_REPOSITORY) - set(_REVIEWED))

        assert missing == [], f"_SITE_REPOSITORY does not resolve: {missing}"
        assert extra == [], f"_SITE_REPOSITORY resolves sites _REVIEWED does not list: {extra}"

    def test_a_repaired_or_safe_verdict_reaches_a_full_replace_repository(self):
        """``REPAIRED``/``SAFE`` on a repository-backed site ⇒ the flag is actually on."""
        merge_mode = sorted(
            site
            for site, dotted in _SITE_REPOSITORY.items()
            if dotted is not None and not _REVIEWED[site].startswith("DEFECT") and not _is_full_replace(dotted)
        )

        assert merge_mode == [], (
            "these sites are recorded as REPAIRED or SAFE but the repository they write to still "
            f"merges, so the None they set is dropped: {merge_mode}"
        )

    def test_a_defect_verdict_is_removed_once_its_repository_is_repaired(self):
        """``DEFECT`` ⇒ the flag is actually off, so the inventory cannot go stale.

        The other direction of the same rule: once a repository is flipped, the
        entry has to be rewritten. Without this half the inventory would keep
        reporting repaired sites as open defects and nobody would notice.
        """
        repaired = sorted(
            site
            for site, dotted in _SITE_REPOSITORY.items()
            if dotted is not None and _REVIEWED[site].startswith("DEFECT") and _is_full_replace(dotted)
        )

        assert repaired == [], (
            "these sites are still recorded as DEFECT but their repository is full-replace now; "
            f"rewrite the verdict to REPAIRED with the issue that did it: {repaired}"
        )

    def test_a_site_with_no_repository_cannot_claim_to_have_been_repaired(self):
        """``None`` means the clear never reaches a stored field — nothing to repair."""
        claiming = sorted(
            site for site, dotted in _SITE_REPOSITORY.items() if dotted is None and _REVIEWED[site].startswith("REPAIR")
        )

        assert claiming == [], f"a site with no repository cannot be REPAIRED: {claiming}"

    def test_the_flag_lookup_can_answer_false(self):
        """Falsification: the derivation must be able to *see* merge mode.

        Every repository in ``_SITE_REPOSITORY`` is full-replace today, so the three
        assertions above would all hold against a ``_is_full_replace`` that returned
        ``True`` unconditionally — vacuously. This pins it against a repository that
        is deliberately still in merge mode.
        """
        assert _is_full_replace("task_repository.ArangoTaskRepository") is True
        assert _is_full_replace("membership_repository.ArangoMembershipRepository") is False
