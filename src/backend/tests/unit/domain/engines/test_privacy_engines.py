"""Tests for REQ-025 privacy engines: DataExport / Erasure / Consent."""

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel

from app.data_access.arango import collections as col
from app.domain.engines.consent_engine import DIARY_AI_ANALYSIS, ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ANONYMIZED_MARKER, ErasureEngine
from app.domain.models.auth import ApiKey, AuthProvider, RefreshToken
from app.domain.models.harvest import HarvestBatch, QualityAssessment, YieldMetric
from app.domain.models.identification import IdentificationRequest
from app.domain.models.ipm import Inspection, TreatmentApplication
from app.domain.models.membership import Membership
from app.domain.models.onboarding import OnboardingState
from app.domain.models.pest_detection import PestDetection
from app.domain.models.pest_image import PestImageContribution
from app.domain.models.plant_diary_entry import PlantDiaryEntry
from app.domain.models.privacy import (
    ConsentRecord,
    DataExportRequest,
    EmailChangeRequest,
    ErasureRequest,
    ErasureStep,
    ProcessingRestriction,
)
from app.domain.models.task import Task
from app.domain.models.user import User
from app.domain.models.user_preference import UserPreference

#: Which domain model backs each collection of the export manifest / the
#: anonymisation rules. Used to check declared field names against reality —
#: see :func:`_model_field_names`.
COLLECTION_MODELS: dict[str, type[BaseModel]] = {
    "users": User,
    "auth_providers": AuthProvider,
    "refresh_tokens": RefreshToken,
    "memberships": Membership,
    "consent_records": ConsentRecord,
    "processing_restrictions": ProcessingRestriction,
    "erasure_requests": ErasureRequest,
    "email_change_requests": EmailChangeRequest,
    "data_export_requests": DataExportRequest,
    "tasks": Task,
    "harvest_batches": HarvestBatch,
    "quality_assessments": QualityAssessment,
    "inspections": Inspection,
    "treatment_applications": TreatmentApplication,
    "plant_diary_entries": PlantDiaryEntry,
    "identification_requests": IdentificationRequest,
}


#: The erasure inventory reaches collections the export manifest does not
#: declare (account plumbing, pest detections, pest reference images). Built
#: explicitly rather than derived from a registry: a document step whose
#: collection is missing here fails the field-existence test by name instead of
#: being skipped (#1663).
ERASURE_COLLECTION_MODELS: dict[str, type[BaseModel]] = {
    **COLLECTION_MODELS,
    "api_keys": ApiKey,
    "user_preferences": UserPreference,
    "onboarding_states": OnboardingState,
    "pest_detections": PestDetection,
    "pest_image_contributions": PestImageContribution,
}


def _model_field_names(model: type[BaseModel]) -> set[str]:
    """Field names of a model, including their aliases (``_key``)."""
    names = set(model.model_fields)
    names |= {field.alias for field in model.model_fields.values() if field.alias}
    return names


class TestDataExportEngine:
    def test_manifest_contains_user_collection(self):
        engine = DataExportEngine()
        manifest = engine.build_export_manifest("u1")
        collections = {entry.collection for entry in manifest}
        assert "users" in collections
        assert "consent_records" in collections
        assert "memberships" in collections

    def test_validate_blocks_when_active_pending(self):
        engine = DataExportEngine()
        existing = [
            DataExportRequest(_key="x", user_key="u1", status="pending"),
        ]
        errors = engine.validate_export_request("u1", existing)
        assert errors

    def test_validate_passes_when_no_active(self):
        engine = DataExportEngine()
        errors = engine.validate_export_request("u1", [])
        assert errors == []

    def test_manifest_includes_identification_requests(self):
        """GDPR-002: Art. 15/20 export must cover plant identification requests."""
        engine = DataExportEngine()
        manifest = engine.build_export_manifest("u1")
        entry = next((e for e in manifest if e.collection == "identification_requests"), None)
        assert entry is not None
        assert entry.filter_field == "user_key"
        assert {"adapter_key", "image_organ", "status", "results", "selected_result_rank", "created_at"} <= set(
            entry.fields
        )
        # image_hash is an internal dedup/audit value and must NOT be exported.
        assert "image_hash" not in entry.fields

    def test_diary_entries_are_exported_with_real_text_and_date(self):
        """REQ-050 AK-24 — Art. 15 disclosure of a diary entry incl. AI result.

        This is the test the old manifest failed: it projected ``body`` and
        ``logged_at``, neither of which exists on ``PlantDiaryEntry``. A wrong
        field name is invisible in an export — an entry with an empty text reads
        exactly like an entry the user never wrote.
        """
        engine = DataExportEngine()
        entry = next(e for e in engine.build_export_manifest("u1") if e.collection == "plant_diary_entries")

        assert entry.filter_field == "created_by"
        # The free text and the date, under the names the model actually uses.
        assert "text" in entry.fields
        assert "created_at" in entry.fields
        assert "body" not in entry.fields
        assert "logged_at" not in entry.fields
        # AK-24: the AI analysis is part of the entry and part of the disclosure.
        assert "analysis" in entry.fields

        # And the projection really produces values on a populated entry.
        diary = PlantDiaryEntry(
            _key="d1",
            plant_key="p1",
            entry_type="observation",
            title="Braune Flecken",
            text="Untere Blätter zeigen braune Flecken.",
            created_by="u1",
            created_at=datetime(2026, 8, 4, 9, 0, tzinfo=UTC),
        )
        projected = {field: getattr(diary, field) for field in entry.fields}
        assert projected["text"] == "Untere Blätter zeigen braune Flecken."
        assert projected["created_at"] == datetime(2026, 8, 4, 9, 0, tzinfo=UTC)

    def test_the_three_retained_categories_are_keyed_on_the_server_set_account_field(self):
        """#1669 — disclosed by key, with the pre-attribution rows stated as a gap.

        Before #1669 these three carried a ``disclosure_gap`` and were keyed on
        the free-text name (``harvester`` …), which no writer fills from an
        account. The key field is server-set on every create path; the gap
        that remains is the rows written before it existed, and the manifest
        must say so rather than presenting the section as complete.
        """
        engine = DataExportEngine()
        by_collection = {e.collection: e for e in engine.build_export_manifest("u1")}
        expected = {
            "harvest_batches": "harvested_by_key",
            "quality_assessments": "assessed_by_key",
            "inspections": "inspected_by_key",
            "treatment_applications": "applied_by_key",
        }
        for collection, key_field in expected.items():
            entry = by_collection[collection]
            assert entry.filter_field == key_field, collection
            assert entry.disclosure_gap is None, collection
            assert entry.attribution_gap, f"{collection}: the legacy null rows must be stated"
            # ``quality_assessments`` carries no ``tenant_key`` (it hangs off its
            # batch), so a tenant clause would match nothing (#1663).
            assert entry.tenant_scoped is (collection != "quality_assessments"), collection
            # The display name is not what the walk keys on, and it is not
            # delivered as if it were an attribution.
            assert entry.filter_field not in ("harvester", "inspector", "applied_by", "assessed_by")
        assert "v0057" in by_collection["quality_assessments"].attribution_gap
        # No production source is undisclosable any more; the mechanism stays
        # (``DataSourceDefinition.disclosure_gap``) for a future category.
        assert not [e.collection for e in by_collection.values() if e.disclosure_gap]

    def test_the_bundle_states_the_attribution_gap_beside_the_delivered_rows(self):
        engine = DataExportEngine()
        source = next(e for e in engine.USER_DATA_MANIFEST if e.collection == "harvest_batches")

        bundle = engine.build_bundle(
            "u1",
            datetime(2026, 9, 23, tzinfo=UTC),
            [(source, [{"batch_id": "HB-1"}])],
            controller_name="c",
            controller_email="c@example.invalid",
        )

        section = bundle["sections"][0]
        assert section["disclosed"] is True
        assert section["not_disclosed_reason"] is None
        assert section["attribution_gap"] == source.attribution_gap
        assert section["record_count"] == 1

    def test_every_manifest_field_exists_on_its_model(self):
        """Guard for the whole manifest, not just the entry REQ-050 touched.

        Four sources carried names that no model has (``tasks.title``,
        ``harvest_batches.name/status/started_at/completed_at``,
        ``inspections.performed_at/findings``,
        ``treatment_applications.dose``) plus two filter fields that matched
        nothing at all (``assigned_to``, ``applicator``). None of that shows up
        at runtime, so it needs a test rather than a reviewer.
        """
        engine = DataExportEngine()
        manifest = engine.build_export_manifest("u1")

        # A new source must extend the mapping — otherwise it escapes the check.
        assert {entry.collection for entry in manifest} == set(COLLECTION_MODELS)

        unknown: list[str] = []
        for entry in manifest:
            allowed = _model_field_names(COLLECTION_MODELS[entry.collection])
            unknown += [f"{entry.collection}.{field}" for field in entry.fields if field not in allowed]
            if entry.filter_field and entry.filter_field not in allowed:
                unknown.append(f"{entry.collection}.[filter]{entry.filter_field}")
        assert unknown == []


class TestErasureEngine:
    def test_build_plan_contains_all_phases(self):
        engine = ErasureEngine()
        plan = engine.build_erasure_plan("u1")

        assert plan.user_key == "u1"
        assert plan.soft_delete_immediate is True
        assert plan.hard_delete_after_days == 90
        assert plan.storage_cleanup
        assert plan.reference_index_cleanup
        assert plan.anonymize
        assert plan.pseudonymize_audit
        assert "users" in plan.delete

    def test_reference_index_cleanup_runs_before_arango_delete(self):
        """REQ-034 SR-003: Phase 0.5 must precede edge/document/user deletion."""
        engine = ErasureEngine()
        plan = engine.build_erasure_plan("u1")

        order = plan.delete
        assert "_reference_index_cleanup" in order
        # Phase 0.5 sits right after Phase 0 storage cleanup and before users.
        assert order.index("_storage_cleanup") < order.index("_reference_index_cleanup")
        assert order.index("_reference_index_cleanup") < order.index("users")

        rule = plan.reference_index_cleanup[0]
        assert rule.store == "pgvector"
        assert rule.collection == "species_embeddings"
        assert "user_contributed" in rule.filter

    def test_tombstone_hash_deterministic(self):
        salt = "x" * 32
        h1 = ErasureEngine.compute_tombstone_hash("u1", salt)
        h2 = ErasureEngine.compute_tombstone_hash("u1", salt)
        assert h1 == h2
        assert h1.startswith("anon_")

    def test_tombstone_hash_rejects_short_salt(self):
        with pytest.raises(ValueError):
            ErasureEngine.compute_tombstone_hash("u1", "short")

    def test_tombstone_hash_distinct_users(self):
        salt = "x" * 32
        assert ErasureEngine.compute_tombstone_hash("u1", salt) != ErasureEngine.compute_tombstone_hash("u2", salt)

    def test_delete_order_includes_identification_requests(self):
        """GDPR-001: Art. 17 erasure must hard-delete plant identification requests.

        identification_requests carries user_key/tenant_key but has no legal
        retention basis, so it must be hard-deleted (in DELETE_ORDER), not
        anonymised.
        """
        engine = ErasureEngine()
        plan = engine.build_erasure_plan("u1")
        assert "identification_requests" in plan.delete
        # Must be deleted before the user document is removed (no orphan refs).
        assert plan.delete.index("identification_requests") < plan.delete.index("users")
        # Must NOT be anonymised — there is no retention obligation.
        anonymized = {rule.collection for rule in plan.anonymize}
        assert "identification_requests" not in anonymized

    def test_diary_entry_user_references_are_anonymised(self):
        """REQ-050 AK-23 / REQ-025 AK-DA-01 — the entry survives, the names do not.

        Before REQ-050 only the *attachments* of a diary entry were covered
        (storage scope ``user_diary_attachments``); the ``plant_diary_entries``
        document had no rule, so the free text of an erased user stayed
        attributable by name.
        """
        engine = ErasureEngine()
        plan = engine.build_erasure_plan("u1")

        diary_rules = [rule for rule in plan.anonymize if rule.collection == "plant_diary_entries"]
        assert {rule.user_field for rule in diary_rules} == {
            "created_by",
            "analysis_requested_by",
            "analysis_claimed_by",
        }
        # Same marker the attachment path writes (AK-OS-02), not "[deleted]".
        assert {rule.anonymized_value for rule in diary_rules} == {ANONYMIZED_MARKER}
        assert ANONYMIZED_MARKER == "_anonymized"

        # The document itself is kept — it belongs to the plant record of a
        # possibly shared tenant. Anonymised, therefore never deleted.
        assert "plant_diary_entries" not in plan.delete

    def test_anonymisation_rules_address_fields_that_exist(self):
        """A rule pointing at a missing field silently anonymises nothing.

        ``treatment_applications`` carried exactly that defect: the rule named
        ``applicator``, while the model has ``applied_by`` — so the applicator of
        a treatment would have kept their name through an erasure.
        """
        engine = ErasureEngine()
        unknown = [
            f"{rule.collection}.{field}"
            for rule in engine.ANONYMIZE_COLLECTIONS
            for field in (rule.user_field, *rule.clear_fields)
            if field not in _model_field_names(COLLECTION_MODELS[rule.collection])
        ]
        assert unknown == []

    def test_the_retention_rules_key_on_the_account_field_and_clear_the_display_name(self):
        """#1669 / #1663 — the free-text rules were inert and are replaced, not kept.

        A rule keyed on ``harvester`` matched whatever was typed and never the
        account being erased. The replacement keys on the server-set field,
        pseudonymises it (the erased user's retained records stay linkable to
        each other for the CanG / PflSchG audit, without naming anyone) and
        clears the display name in the same write — a name is personal data on
        its own. No rule may key on a display field any more.
        """
        engine = ErasureEngine()
        pseudonymised = [rule for rule in engine.ANONYMIZE_COLLECTIONS if rule.replacement_strategy != "marker"]
        rules = {rule.collection: rule for rule in pseudonymised}
        expected = {
            "harvest_batches": ("harvested_by_key", "harvester"),
            "quality_assessments": ("assessed_by_key", "assessed_by"),
            "inspections": ("inspected_by_key", "inspector"),
            "treatment_applications": ("applied_by_key", "applied_by"),
        }
        assert set(rules) == set(expected)
        for collection, (key_field, display_field) in expected.items():
            rule = rules[collection]
            assert rule.user_field == key_field
            assert rule.replacement_strategy == "tombstone_hash"
            assert rule.clear_fields == [display_field]
        display_keyed = [
            f"{rule.collection}.{rule.user_field}"
            for rule in engine.ANONYMIZE_COLLECTIONS
            if rule.user_field in ("harvester", "inspector", "applied_by", "assessed_by")
        ]
        assert display_keyed == [], "an inert free-text rule survived beside the key rule"
        # Exactly one rule per retained collection: replaced, not duplicated.
        for collection in expected:
            assert sum(1 for rule in engine.ANONYMIZE_COLLECTIONS if rule.collection == collection) == 1

    def test_yield_metrics_carries_no_user_field_and_therefore_no_rule(self):
        """#1663 — NFR-011 R-16 names ``yield_metrics``, but there is nobody in it.

        Measured: ``YieldMetric`` holds weights, a waste percentage and its
        batch key. An anonymisation rule needs a field to match the subject on;
        declaring one here would address a field that does not exist. Should a
        user reference ever be added to the model, this goes red and the rule
        has to be written.
        """
        user_like = [
            name
            for name in YieldMetric.model_fields
            if name.endswith(("_by", "_by_key", "user_key")) or name in ("created_by", "owner")
        ]
        assert user_like == []
        assert "yield_metrics" not in {rule.collection for rule in ErasureEngine.ANONYMIZE_COLLECTIONS}

    def test_anonymized_collection_names_are_reported_once(self):
        """AK-08a — the confirmation lists categories, not rules."""
        engine = ErasureEngine()
        names = engine.anonymized_collection_names()

        assert names.count("plant_diary_entries") == 1
        assert len(names) == len(set(names))
        assert set(names) == {rule.collection for rule in engine.ANONYMIZE_COLLECTIONS}


class TestErasureStepUserField:
    """#1663 — every step that filters a collection says which field it filters on."""

    def test_every_document_step_user_field_exists_on_its_model(self):
        """A step keyed on a missing field deletes nothing and reports success.

        The collection->model map is explicit (``ERASURE_COLLECTION_MODELS``);
        a document step whose collection has no entry fails here by name —
        a ``.get()`` that skipped it would be the vacuum this test exists for.
        """
        unmapped: list[str] = []
        unknown: list[str] = []
        for step in ErasureEngine.DELETE_STEPS:
            if step.kind != "document":
                continue
            model = ERASURE_COLLECTION_MODELS.get(step.collection)
            if model is None:
                unmapped.append(step.collection)
                continue
            if step.user_field not in _model_field_names(model):
                unknown.append(f"{step.collection}.{step.user_field}")
        assert unmapped == [], "extend ERASURE_COLLECTION_MODELS for these document steps"
        assert unknown == []

    def test_every_anonymisation_and_pseudonymisation_field_exists_on_its_model(self):
        """``user_field`` and every ``clear_fields`` entry, for all rules — no skip."""
        rules = [
            *((rule.collection, rule.user_field, rule.clear_fields) for rule in ErasureEngine.ANONYMIZE_COLLECTIONS),
            *((rule.collection, rule.user_field, []) for rule in ErasureEngine.PSEUDONYMIZE_AUDIT_COLLECTIONS),
        ]
        unmapped = [collection for collection, _f, _c in rules if collection not in ERASURE_COLLECTION_MODELS]
        assert unmapped == []
        unknown = [
            f"{collection}.{field}"
            for collection, user_field, clear_fields in rules
            for field in (user_field, *clear_fields)
            if field not in _model_field_names(ERASURE_COLLECTION_MODELS[collection])
        ]
        assert unknown == []

    def test_every_edge_endpoint_matches_the_graph_definition(self):
        """The direction is measured against the named graph, not assumed.

        A prior manifest bug declared ``membership_in`` as if it touched the
        user; it runs ``memberships -> tenants``. Without ``via`` the declared
        endpoint must be able to hold ``users/<key>``; with ``via`` it must be
        able to hold a document of that collection.
        """
        definitions = {d["edge_collection"]: d for d in col.GRAPH_EDGE_DEFINITIONS}
        wrong: list[str] = []
        for step in ErasureEngine.DELETE_STEPS:
            if step.kind != "edge":
                continue
            definition = definitions.get(step.collection)
            assert definition is not None, f"edge step '{step.collection}' is not in the named graph"
            side = "from_vertex_collections" if step.user_field == "_from" else "to_vertex_collections"
            expected = step.via or col.USERS
            if expected not in definition[side]:
                wrong.append(f"{step.collection}.{step.user_field} -> {definition[side]} (expected {expected})")
        assert wrong == []

    def test_a_via_edge_precedes_the_document_step_that_matches_its_endpoint(self):
        """The executor resolves a ``via`` edge through its parent documents.

        Removing ``memberships`` first leaves nothing for ``membership_in`` to
        be matched against — the edges would survive as orphans.
        """
        order = ErasureEngine.delete_order()
        documents = {step.collection: step for step in ErasureEngine.DELETE_STEPS if step.kind == "document"}
        vias = [step for step in ErasureEngine.DELETE_STEPS if step.kind == "edge" and step.via]
        assert vias, "guard against a vacuous loop: membership_in and the pest-detection edges use via"
        for step in vias:
            assert step.via in documents, f"'{step.collection}' is reached via '{step.via}', which has no document step"
            assert order.index(step.collection) < order.index(step.via), step.collection

    def test_every_user_keyed_step_runs_before_the_audit_pseudonymisation(self):
        """#1663 — after ``erasure_requests.user_key`` is hashed, the key is gone.

        Every step that finds its rows by the subject's key — edges, documents
        and the anonymisation phase — has to have run by then; the user
        document comes last.
        """
        order = ErasureEngine.delete_order()
        audit = order.index("_pseudonymize_audit_collections")
        keyed = [step.collection for step in ErasureEngine.DELETE_STEPS if step.kind in ("edge", "document")]
        assert keyed, "guard against a vacuous loop"
        late = [name for name in [*keyed, "_anonymize_collections"] if order.index(name) > audit]
        assert late == []
        assert order[-1] == "users"

    @pytest.mark.parametrize("kind", ["edge", "document"])
    def test_a_filtered_step_without_a_user_field_is_refused(self, kind):
        with pytest.raises(ValueError, match="user_field"):
            ErasureStep(collection="x", kind=kind, executor="account_erasure")

    @pytest.mark.parametrize("kind", ["user", "phase"])
    def test_a_user_or_phase_step_takes_no_user_field(self, kind):
        with pytest.raises(ValueError, match="filters nothing"):
            ErasureStep(collection="x", kind=kind, executor="account_erasure", user_field="user_key")

    def test_an_edge_keyed_on_a_document_field_is_refused(self):
        with pytest.raises(ValueError, match="_from or _to"):
            ErasureStep(collection="has_x", kind="edge", executor="account_erasure", user_field="user_key")

    def test_a_document_keyed_on_an_edge_endpoint_is_refused(self):
        with pytest.raises(ValueError, match="edge endpoint"):
            ErasureStep(collection="x", kind="document", executor="account_erasure", user_field="_from")

    def test_via_is_refused_on_a_document(self):
        with pytest.raises(ValueError, match="via applies to edges only"):
            ErasureStep(collection="x", kind="document", executor="account_erasure", user_field="user_key", via="y")


class TestErasurePhaseNames:
    """#1664 — the executor recognises the two ArangoDB phases by name."""

    def test_both_phase_constants_name_a_declared_phase_step(self):
        phases = {s.collection for s in ErasureEngine.DELETE_STEPS if s.kind == "phase"}
        assert ErasureEngine.ANONYMIZE_PHASE in phases
        assert ErasureEngine.PSEUDONYMIZE_AUDIT_PHASE in phases

    def test_every_phase_is_either_an_arango_phase_or_owned_by_a_non_arango_executor(self):
        """A phase the ArangoDB executor neither implements nor delegates would be refused at runtime."""
        arango = {ErasureEngine.ANONYMIZE_PHASE, ErasureEngine.PSEUDONYMIZE_AUDIT_PHASE}
        unhandled = [
            s.collection
            for s in ErasureEngine.DELETE_STEPS
            if s.kind == "phase"
            and s.collection not in arango
            and s.executor not in ("storage_cleanup", "reference_index_cleanup")
        ]
        assert unhandled == []


class TestConsentEngine:
    def test_required_purpose_always_allowed(self):
        engine = ConsentEngine()
        assert engine.is_processing_allowed("core_functionality", consent=None) is True

    def test_optional_purpose_blocked_without_consent(self):
        engine = ConsentEngine()
        assert engine.is_processing_allowed("error_tracking", consent=None) is False

    def test_revoking_required_returns_error(self):
        engine = ConsentEngine()
        errors = engine.validate_consent_change("core_functionality", grant=False)
        assert errors

    def test_unknown_purpose_returns_error(self):
        engine = ConsentEngine()
        errors = engine.validate_consent_change("does_not_exist", grant=True)
        assert errors

    def test_known_optional_purposes(self):
        engine = ConsentEngine()
        keys = {p.key for p in engine.get_all_purposes()}
        assert {"core_functionality", "error_tracking", "hibp_check", "external_enrichment"} <= keys

    def test_diary_ai_analysis_purpose_registered(self):
        """REQ-050 §7.1 — the purpose must be known, optional and revocable."""
        engine = ConsentEngine()
        purpose = engine.find_purpose(DIARY_AI_ANALYSIS)

        assert purpose is not None
        assert purpose.required is False
        assert purpose.legal_basis.startswith("Art. 6(1)(a)")
        # Revocable: a required purpose could not be withdrawn (AK-13 of REQ-025).
        assert engine.validate_consent_change(DIARY_AI_ANALYSIS, grant=False) == []
        # DE and EN label + description are both present (AK-28).
        assert purpose.label_de and purpose.label_en
        assert purpose.description_de and purpose.description_en

    def test_diary_ai_analysis_follows_grant_and_revocation(self):
        """AK-13 — no record and a revoked record both mean "not allowed"."""
        engine = ConsentEngine()
        granted = ConsentRecord(user_key="u1", purpose=DIARY_AI_ANALYSIS, granted=True)
        revoked = ConsentRecord(
            user_key="u1",
            purpose=DIARY_AI_ANALYSIS,
            granted=False,
            revoked_at=datetime.now(UTC),
        )

        assert engine.is_processing_allowed(DIARY_AI_ANALYSIS, consent=None) is False
        assert engine.is_processing_allowed(DIARY_AI_ANALYSIS, consent=granted) is True
        assert engine.is_processing_allowed(DIARY_AI_ANALYSIS, consent=revoked) is False

    def test_diary_ai_analysis_is_independent_of_the_ai_assistant_purposes(self):
        """§7.1 — neither consent implies the other, and cloud does not apply."""
        engine = ConsentEngine()
        diary_granted = ConsentRecord(user_key="u1", purpose=DIARY_AI_ANALYSIS, granted=True)

        # Granting the diary purpose says nothing about the server-side assistant.
        assert engine.is_processing_allowed("ai_tenant_data_access", consent=None) is False
        assert engine.is_processing_allowed("ai_cloud_processing", consent=None) is False
        assert engine.is_processing_allowed(DIARY_AI_ANALYSIS, consent=diary_granted) is True

    def test_plant_diagnosis_purpose_registered(self):
        engine = ConsentEngine()
        purpose = engine.find_purpose("plant_diagnosis")
        assert purpose is not None
        assert purpose.required is False
        # optional purpose: blocked without consent, allowed once granted
        assert engine.is_processing_allowed("plant_diagnosis", consent=None) is False


class TestErasureConfirmationAndTombstoneShape:
    """#1645 — helpers the scheduled erasure and its confirmation read."""

    def test_deleted_names_are_the_document_and_user_steps_in_declared_order(self):
        names = ErasureEngine().deleted_collection_names()
        expected = [s.collection for s in ErasureEngine.DELETE_STEPS if s.kind in ("document", "user")]
        assert names == expected
        assert names[-1] == "users"
        assert not any(name.startswith("_") for name in names), "a phase is not a category"

    def test_a_computed_tombstone_is_recognised(self):
        assert ErasureEngine.is_tombstone(ErasureEngine.compute_tombstone_hash("u-1", "s" * 32))

    @pytest.mark.parametrize(
        "value",
        ["u-1", "anon_", "anon_0123456789abcdeZ", "anon_0123456789abcdef0", "xanon_0123456789abcdef", ""],
    )
    def test_anything_else_is_not(self, value):
        assert not ErasureEngine.is_tombstone(value)
