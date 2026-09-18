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

**What it measures.** Every function under ``app/domain/services`` that both

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

**A spelling it does not match** (stated rather than discovered later): a clear
routed through a helper (``self._clear(entry)`` writing the ``None`` in another
function), a ``setattr(obj, name, None)``, or a ``None`` that arrives as a
parameter's default and is never written literally in the body. The first is the
realistic one; ``_REVIEWED`` is therefore a floor on the class, not a proof of its
size. Two of the entries below (``dormancy_care_activator.activate`` and
``care_reminder_service.confirm_reminder``) are only visible at all because the
scan resolves locals bound to ``None``.
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.support.execution_guards import find_project_root

_SERVICES = find_project_root(Path(__file__)) / "app" / "domain" / "services"

#: Field-clearing writes reaching these are *not* dropped: they end in
#: ``_update_doc_fields``, which passes ``keep_none=True``.
_KEEP_NONE_METHODS = frozenset({"update_fields", "update_fields_checked"})

#: The measured inventory: ``module::function`` → the verdict, written out.
#:
#: ``REPAIRED`` — this change made the target repository full-replace, so the clear lands.
#: ``SAFE`` — the repository was already full-replace, the write path already keeps
#: nulls, or the ``None`` never reaches a stored field at all.
#: ``DEFECT #NNNN`` — measured to be dropped; tracked in its own issue, because
#: flipping a repository needs its own writer×fields table and red-first pass
#: (which is what #1506 was for ``care_profiles``), not a drive-by edit.
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
    # ── measured defects of the same class, tracked in #1516 ─────────────────
    #
    # Each repository is its own change: flipping `_update_is_full_replace` alters
    # null semantics for every writer of that collection, so each needs the
    # writer×fields table and the red-first pass #1506 did for care_profiles. They
    # are listed individually rather than as one line so a fix can retire its own
    # entry without touching the others.
    "user_service::delete_account": (
        "DEFECT #1516 — the soft-delete nulls User.password_hash and avatar_url; the merge-mode "
        "update keeps the credential hash on an account meant to have none."
    ),
    "privacy_service::request_erasure": ("DEFECT #1516 — the same soft-delete on the DSGVO erasure path."),
    "privacy_service::grant_consent": (
        "DEFECT #1516 — re-granting a revoked consent nulls revoked_at and writes through "
        "ArangoConsentRepository.update (merge mode): the record still carries its revocation."
    ),
    "task_service::reopen_task": (
        "DEFECT #1516 — a reopened task nulls completed_at, actual_duration_minutes, "
        "completion_notes, difficulty_rating and quality_rating; all five survive."
    ),
    "phase_service::delete_phase_history": (
        "DEFECT #1516 — reopening the previous phase nulls exited_at/actual_duration_days through "
        "update_phase_history (merge mode), so the reopened phase stays closed. Its sibling "
        "clears on the PlantInstance (current_phase_key/_started_at) do land — that repository "
        "is full-replace — which is why the function looks half-correct."
    ),
    "phase_service::update_phase_history_dates": (
        "DEFECT #1516 — nulls actual_duration_days when the exit date is removed; same path."
    ),
    "planting_run_service::batch_update_phase_dates": ("DEFECT #1516 — the same clear on the batch path."),
    "onboarding_service::reset_wizard": (
        "DEFECT #1516 — the wizard reset nulls completed_at, site_type, selected_site_key, "
        "selected_kit_id, selected_experience_level and plant_count; a merge-mode update keeps "
        "them, so the 'reset' wizard reopens on the previous run's selections."
    ),
    "onboarding_service::ensure_onboarding_state_for_user": (
        "DEFECT #1516 — nulls completed_at on the same merge-mode repository."
    ),
    "notification_propagation_service::_update_single": (
        "DEFECT #1516 — under `reset_read` it nulls read_at/acted_at so the row re-surfaces in "
        "the badge, and ArangoNotificationRepository merges: the row stays read (#769's path)."
    ),
}


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
    for path in sorted(_SERVICES.rglob("*.py")):
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
