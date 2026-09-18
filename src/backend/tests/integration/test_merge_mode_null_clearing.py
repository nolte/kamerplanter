"""#1525 / #1516 — six more collections whose writers could not clear a field.

``BaseArangoRepository._update_is_full_replace`` is ``False`` by default. In that
**merge** mode ``_update_doc`` dumps the model with ``exclude_none=True`` and calls
``collection.update(..., keep_none=True)``, so a field the writer set to ``None``
is absent from the payload and the stored value survives an update that meant to
clear it. The write answers 200 with the old value; nothing warns.

#1506 measured that for ``care_profiles`` (``test_care_profile_null_clearing.py``).
This file is the same measurement for the six collections the #1516 class sweep
found, with the credential pair of #1525 first:

* ``users`` — a soft-deleted account kept its bcrypt ``password_hash`` and its
  ``avatar_url`` while ``is_active``/``email``/``display_name`` *were* written, so
  the record read as deleted. On the DSGVO Art. 17 path the credential outlived
  the erasure request by the 90 days until the hard delete (NFR-011 R-01). The
  same drop silently defeated ``ArangoUserRepository.update_fields``, which is a
  full-model write here and not the base class's ``keep_none=True`` merge: a used
  ``password_reset_token`` was never burned.
* ``consent_records`` — a re-granted consent kept the timestamp of its revocation.
* ``tasks`` — a reopened task kept its whole completion record.
* ``phase_histories`` — the phase a deletion was supposed to reopen stayed closed.
* ``onboarding_states`` — a wizard "reset" reopened on the previous run's answers.
* ``notifications`` — a note that should re-surface stayed read and out of the badge.

**Why this file needs a real ArangoDB.** The defect *is* the driver/server null
handling: which attributes ``collection.update`` removes, keeps or ignores under
``keepNull``. A repository double is free to invent that semantics — the failure
class a ``_FakeDb`` would hide here. Only the server can answer whether the
attribute is gone from the stored document, which is why every assertion below
reads the **raw** document by AQL rather than the model (every field is
``X | None``, so a model read cannot tell "removed" from "still there, holding
null" — and both would pass while only one proves the write reached the server).

Each collection also asserts that an attribute the model does **not** declare
survives the write. That is the claim the whole design rests on: full-replace is
still a *merge* at the storage level, so ``tenant_key`` (stamped by
``app/migrations/backfill_tenant_key.py`` onto documents whose model has no such
field) and any legacy attribute keep their stored value; only an explicit ``null``
removes its attribute.

Run with: pytest tests/integration/test_merge_mode_null_clearing.py -v
(requires an ArangoDB; see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#1525/#1516 are a driver/server null-handling contract; no double may answer it"),
]

_DB_NAME = "kamerplanter_merge_mode_null_test"
_TENANT_KEY = "tenant-alpha"
_USER_KEY = "user-erika"

#: Attributes every seeded document carries that its model does not declare.
#:
#: ``tenant_key`` is the real one on the collections whose model has no such field;
#: ``legacy_attr`` stands for anything an older schema left behind. Both must
#: survive a full-replace write — measured, not asserted in a comment.
_UNDECLARED = {"legacy_attr": "written-by-an-older-schema"}


def _settings():
    from app.config.settings import Settings

    return Settings(arangodb_database=_DB_NAME)


def _raw(db, collection: str, key: str) -> dict:
    """The stored document as the server holds it — an *absent* attribute is visible."""
    doc = db.collection(collection).get(key)
    assert doc is not None, f"{collection}/{key} disappeared"
    return doc


@pytest.fixture
def db():
    """A bootstrapped test database, dropped afterwards."""
    from app.data_access.arango.collections import ensure_collections
    from app.data_access.arango.connection import ArangoConnection

    conn = ArangoConnection(_settings())
    database = conn.connect()
    ensure_collections(database)
    yield database
    conn.close()
    system = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)


# ── users (#1525) ────────────────────────────────────────────────────────────


#: What the stored user holds before each write under test. Every nullable the
#: measured paths touch is populated, so "the writer meant ``None``" and "the
#: stored value survived" are distinguishable for each of them.
_STORED_USER = {
    "email": "erika@example.org",
    "display_name": "Erika Mustermann",
    # A real bcrypt hash shape — this is the datum #1525 is about.
    "password_hash": "$2b$12$abcdefghijklmnopqrstuv0123456789ABCDEFGHIJKLMNOPQRSTU",
    "avatar_url": "https://cdn.example.org/avatars/erika.png",
    "password_reset_token": "reset-token-still-valid-for-an-hour",
    "email_verification_token": "verification-token",
    "is_active": True,
    "locale": "de",
    "created_at": "2026-01-01T00:00:00+00:00",
}


def _user_repo(db):
    from app.data_access.arango.user_repository import ArangoUserRepository

    return ArangoUserRepository(db)


@pytest.fixture
def user_key(db) -> str:
    from app.data_access.arango import collections as col

    db.collection(col.USERS).insert({"_key": _USER_KEY, **_STORED_USER, **_UNDECLARED, "tenant_key": _TENANT_KEY})
    return _USER_KEY


def _user_service(db):
    """The real service on the real repositories — the production write path."""
    from app.data_access.arango.refresh_token_repository import ArangoRefreshTokenRepository
    from app.domain.services.user_service import UserService

    return UserService(_user_repo(db), ArangoRefreshTokenRepository(db))


def _privacy_service(db):
    """``PrivacyService`` wired for the two paths measured here.

    ``request_erasure`` reaches ``user_repo``, ``erasure_repo``,
    ``refresh_token_repo``, ``password_engine`` and ``erasure_engine``;
    ``grant_consent`` reaches ``consent_repo`` and ``consent_engine``. The
    remaining collaborators are real objects too wherever they need no I/O, so no
    double on this path can invent a shape the production wiring does not have.
    """
    from app.data_access.arango.consent_repository import ArangoConsentRepository
    from app.data_access.arango.data_export_repository import ArangoDataExportRepository
    from app.data_access.arango.email_change_repository import ArangoEmailChangeRepository
    from app.data_access.arango.erasure_repository import ArangoErasureRepository
    from app.data_access.arango.processing_restriction_repository import ArangoProcessingRestrictionRepository
    from app.data_access.arango.refresh_token_repository import ArangoRefreshTokenRepository
    from app.domain.engines.consent_engine import ConsentEngine
    from app.domain.engines.data_export_engine import DataExportEngine
    from app.domain.engines.erasure_engine import ErasureEngine
    from app.domain.engines.password_engine import PasswordEngine
    from app.domain.engines.token_engine import TokenEngine
    from app.domain.services.privacy_service import PrivacyService

    class _SilentEmailService:
        """The erasure path sends nothing; a raising stub would mask a real call."""

        def __getattr__(self, _name):
            return lambda *args, **kwargs: None

    return PrivacyService(
        export_repo=ArangoDataExportRepository(db),
        consent_repo=ArangoConsentRepository(db),
        restriction_repo=ArangoProcessingRestrictionRepository(db),
        erasure_repo=ArangoErasureRepository(db),
        email_change_repo=ArangoEmailChangeRepository(db),
        user_repo=_user_repo(db),
        refresh_token_repo=ArangoRefreshTokenRepository(db),
        data_export_engine=DataExportEngine(),
        erasure_engine=ErasureEngine(),
        consent_engine=ConsentEngine(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine(secret_key="integration-test-secret-not-a-credential"),
        email_service=_SilentEmailService(),
        frontend_url="http://localhost:5173",
    )


class TestTheSoftDeleteRemovesTheCredential:
    """#1525: the two soft-delete paths, measured on the stored document."""

    @pytest.mark.parametrize("field", ["password_hash", "avatar_url"])
    def test_delete_account_clears_it(self, db, user_key, field):
        """Against the merge-mode repository both assertions failed with the stored value."""
        from app.data_access.arango import collections as col

        _user_service(db).delete_account(user_key)

        assert _raw(db, col.USERS, user_key).get(field) is None, f"a deleted account kept its {field}"

    def test_delete_account_still_writes_the_fields_that_always_landed(self, db, user_key):
        """The three fields that *did* land are what made the record read as deleted.

        Asserted here so "the clear works now" cannot be bought by breaking the
        rest of the same write.
        """
        from app.data_access.arango import collections as col

        _user_service(db).delete_account(user_key)

        stored = _raw(db, col.USERS, user_key)
        assert stored["is_active"] is False
        assert stored["email"] == f"deleted_{user_key}@deleted.example.com"
        assert stored["display_name"] == "Deleted User"

    def test_request_erasure_clears_the_credential(self, db, user_key):
        """DSGVO Art. 17: the hash may not outlive the request by the 90-day window.

        ``request_erasure`` re-authenticates against ``password_hash`` *before* the
        write, so the order matters and is exercised here: the confirmation is
        checked against the stored hash, and only then is the hash removed.
        """
        from app.data_access.arango import collections as col
        from app.domain.engines.password_engine import PasswordEngine

        password = "correct horse battery staple"
        db.collection(col.USERS).update({"_key": user_key, "password_hash": PasswordEngine().hash_password(password)})

        _privacy_service(db).request_erasure(user_key, password)

        stored = _raw(db, col.USERS, user_key)
        assert stored.get("password_hash") is None, "an account awaiting erasure kept its credential"
        assert stored["is_active"] is False

    def test_update_fields_clears_a_used_reset_token(self, db, user_key):
        """``update_fields`` is a full-model write here, so it needs the flag too.

        ``AuthService.reset_password`` and ``change_password`` both clear
        ``password_reset_token``/``password_reset_expires`` through this method and
        say in a comment that they rely on the explicit ``None`` being persisted.
        They did not: the override re-materialises a full ``User`` and goes through
        the merge-mode ``update``, so a used reset token stayed valid for its full
        hour — the very window the owner rotated the password to close.
        """
        from app.data_access.arango import collections as col

        _user_repo(db).update_fields(
            user_key,
            {"password_hash": "$2b$12$new", "password_reset_token": None, "password_reset_expires": None},
        )

        stored = _raw(db, col.USERS, user_key)
        assert stored.get("password_reset_token") is None, "a used password-reset token survived the reset"
        assert stored["password_hash"] == "$2b$12$new"

    def test_an_attribute_the_user_model_does_not_declare_survives(self, db, user_key):
        """Full-replace removes an explicit ``null``; it does not replace the document."""
        from app.data_access.arango import collections as col

        _user_service(db).delete_account(user_key)

        stored = _raw(db, col.USERS, user_key)
        assert stored["legacy_attr"] == _UNDECLARED["legacy_attr"]
        assert stored["tenant_key"] == _TENANT_KEY

    def test_the_soft_delete_does_not_drop_a_field_it_never_names(self, db, user_key):
        """``locale`` is neither cleared nor mentioned — it must read back unchanged.

        The risk full-replace introduces is the mirror image of the defect: a writer
        that hands over a model missing a field would now *erase* it. Every writer of
        ``users`` starts from the stored model, and this is that claim measured.
        """
        from app.data_access.arango import collections as col

        _user_service(db).delete_account(user_key)

        stored = _raw(db, col.USERS, user_key)
        assert stored["locale"] == "de"
        # ``created_at`` is popped from the payload in full-replace mode, so the
        # stored timestamp is not rewritten at all — it comes back byte-identical.
        # (In merge mode this assertion fails for a *different* reason: the model
        # round-trip re-serialises it into Pydantic's JSON form.)
        assert stored["created_at"] == _STORED_USER["created_at"], "full-replace mode must not rewrite created_at"


# ── consent_records (#1516) ──────────────────────────────────────────────────


class TestARegrantedConsentDropsItsRevocation:
    def test_grant_consent_clears_revoked_at(self, db, user_key):
        from app.data_access.arango import collections as col

        purpose = "error_tracking"
        meta = db.collection(col.CONSENT_RECORDS).insert(
            {
                "user_key": user_key,
                "purpose": purpose,
                "granted": False,
                "granted_at": "2026-01-01T00:00:00+00:00",
                "revoked_at": "2026-02-01T00:00:00+00:00",
                "ip_address": "203.0.113.7",
                "user_agent": "Mozilla/5.0 (the browser that revoked it)",
                **_UNDECLARED,
            }
        )

        _privacy_service(db).grant_consent(user_key, purpose)

        stored = _raw(db, col.CONSENT_RECORDS, meta["_key"])
        assert stored["granted"] is True
        assert stored.get("revoked_at") is None, "a re-granted consent still carried its revocation"
        # The new grant supplied no IP/agent, so the previous grant's must not be
        # re-attributed to it (REQ-025: the record documents *this* declaration).
        assert stored.get("ip_address") is None
        assert stored.get("user_agent") is None
        assert stored["legacy_attr"] == _UNDECLARED["legacy_attr"]


# ── tasks (#1516) ────────────────────────────────────────────────────────────


#: The completion record ``reopen_task`` clears, all five fields of it.
_COMPLETION = {
    "completed_at": "2026-03-01T10:00:00+00:00",
    "actual_duration_minutes": 45,
    "completion_notes": "Umgetopft, Wurzelballen war durchwurzelt",
    "difficulty_rating": 4,
    "quality_rating": 5,
}


class TestAReopenedTaskDropsItsCompletionRecord:
    @pytest.fixture
    def task_key(self, db) -> str:
        from app.data_access.arango import collections as col

        meta = db.collection(col.TASKS).insert(
            {
                "tenant_key": _TENANT_KEY,
                "name": "Repot the Monstera",
                "status": "completed",
                "photo_refs": ["att-1"],
                **_COMPLETION,
                **_UNDECLARED,
            }
        )
        return str(meta["_key"])

    def _service(self, db):
        from app.data_access.arango.task_repository import ArangoTaskRepository
        from app.domain.engines.dependency_resolver import DependencyResolver
        from app.domain.engines.hst_validator import HSTValidator
        from app.domain.services.task_service import TaskService

        return TaskService(ArangoTaskRepository(db), HSTValidator(), DependencyResolver())

    @pytest.mark.parametrize("field", sorted(_COMPLETION))
    def test_reopen_task_clears_it(self, db, task_key, field):
        from app.data_access.arango import collections as col

        self._service(db).reopen_task(task_key, tenant_key=_TENANT_KEY)

        assert _raw(db, col.TASKS, task_key).get(field) is None, f"a reopened task kept its {field}"

    def test_reopen_task_keeps_what_it_does_not_clear(self, db, task_key):
        """``photo_refs`` and the reopen markers are the other half of the same write."""
        from app.data_access.arango import collections as col

        self._service(db).reopen_task(task_key, tenant_key=_TENANT_KEY)

        stored = _raw(db, col.TASKS, task_key)
        assert stored["status"] == "pending"
        assert stored["photo_refs"] == ["att-1"]
        assert stored["reopened_from_status"] == "completed"
        assert stored["legacy_attr"] == _UNDECLARED["legacy_attr"]


# ── phase_histories (#1516) ──────────────────────────────────────────────────


class TestDeletingTheOpenPhaseReopensThePreviousOne:
    _PLANT_KEY = "plant-monstera"

    @pytest.fixture
    def history_keys(self, db) -> tuple[str, str]:
        """A closed vegetative entry and the open flowering entry that follows it."""
        from app.data_access.arango import collections as col

        db.collection(col.PLANT_INSTANCES).insert(
            {
                "_key": self._PLANT_KEY,
                "tenant_key": _TENANT_KEY,
                "instance_id": f"P-{self._PLANT_KEY}",
                "species_key": "monstera-deliciosa",
                "plant_name": "Monstera",
                "planted_on": "2026-01-01",
                "current_phase_key": "phase-flowering",
                "current_phase_started_at": "2026-03-01T00:00:00+00:00",
            }
        )
        previous = db.collection(col.PHASE_HISTORIES).insert(
            {
                "plant_instance_key": self._PLANT_KEY,
                "phase_key": "phase-vegetative",
                "phase_name": "Vegetative",
                "entered_at": "2026-01-01T00:00:00+00:00",
                "exited_at": "2026-03-01T00:00:00+00:00",
                "actual_duration_days": 59,
                "performance_score": 82.5,
                **_UNDECLARED,
            }
        )
        current = db.collection(col.PHASE_HISTORIES).insert(
            {
                "plant_instance_key": self._PLANT_KEY,
                "phase_key": "phase-flowering",
                "phase_name": "Flowering",
                "entered_at": "2026-03-01T00:00:00+00:00",
            }
        )
        for meta in (previous, current):
            db.collection(col.PHASE_HISTORY_EDGE).insert(
                {
                    "_from": f"{col.PLANT_INSTANCES}/{self._PLANT_KEY}",
                    "_to": f"{col.PHASE_HISTORIES}/{meta['_key']}",
                }
            )
        return str(previous["_key"]), str(current["_key"])

    def _service(self, db):
        from app.data_access.arango.lifecycle_repository import ArangoLifecycleRepository
        from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
        from app.domain.services.phase_service import PhaseService

        return PhaseService(ArangoLifecycleRepository(db), ArangoPlantInstanceRepository(db))

    @pytest.mark.parametrize("field", ["exited_at", "actual_duration_days"])
    def test_the_reopened_phase_is_actually_open(self, db, history_keys, field):
        """Against the merge-mode repository the reopened phase stayed closed."""
        from app.data_access.arango import collections as col

        previous_key, current_key = history_keys

        self._service(db).delete_phase_history(self._PLANT_KEY, current_key)

        assert _raw(db, col.PHASE_HISTORIES, previous_key).get(field) is None, (
            f"the reopened phase kept its {field} and is still closed"
        )

    def test_the_reopened_phase_keeps_everything_else(self, db, history_keys):
        from app.data_access.arango import collections as col

        previous_key, current_key = history_keys

        self._service(db).delete_phase_history(self._PLANT_KEY, current_key)

        stored = _raw(db, col.PHASE_HISTORIES, previous_key)
        assert stored["phase_name"] == "Vegetative"
        assert stored["performance_score"] == 82.5
        assert stored["legacy_attr"] == _UNDECLARED["legacy_attr"]

    def test_closing_a_phase_does_not_erase_a_field_the_engine_never_names(self, db, history_keys):
        """``PhaseTransitionEngine`` used to re-list ten of the model's twelve fields.

        ``performance_score`` was not among them, so under full-replace closing a
        phase would have *erased* it — the mirror-image risk the flag introduces.
        The engine derives its model with ``model_copy`` since #1516, and this is
        that claim measured rather than argued.
        """
        from app.data_access.arango import collections as col
        from app.data_access.arango.lifecycle_repository import ArangoLifecycleRepository
        from app.domain.models.phase import PhaseHistory

        previous_key, _ = history_keys
        repo = ArangoLifecycleRepository(db)
        # Reopen it the way ``delete_phase_history`` does, then close it again
        # through the engine's own write.
        stored = PhaseHistory(**repo._from_doc(_raw(db, col.PHASE_HISTORIES, previous_key)))
        repo.update_phase_history(
            previous_key,
            stored.model_copy(update={"exited_at": datetime(2026, 4, 1, tzinfo=UTC), "actual_duration_days": 90}),
        )

        assert _raw(db, col.PHASE_HISTORIES, previous_key)["performance_score"] == 82.5


# ── onboarding_states (#1516) ────────────────────────────────────────────────


#: What ``reset_wizard`` nulls. Every one of them survived the reset before #1516,
#: while the list-valued resets in the same dict landed (``[]`` is not ``None``) —
#: which is why the reset looked like it worked.
_WIZARD_SELECTIONS = {
    "completed_at": "2026-02-01T12:00:00+00:00",
    "selected_kit_id": "kit-herbs",
    "selected_experience_level": "beginner",
    "site_type": "indoor",
    "selected_site_key": "site-kitchen",
    "plant_count": 3,
}


class TestAWizardResetForgetsThePreviousRun:
    @pytest.fixture
    def state_key(self, db) -> str:
        from app.data_access.arango import collections as col

        meta = db.collection(col.ONBOARDING_STATES).insert(
            {
                "user_key": _USER_KEY,
                "completed": True,
                "skipped": False,
                "wizard_step": 6,
                "site_name": "Kitchen windowsill",
                "favorite_species_keys": ["ocimum-basilicum"],
                **_WIZARD_SELECTIONS,
                **_UNDECLARED,
            }
        )
        return str(meta["_key"])

    def _service(self, db):
        from app.domain.services.onboarding_service import OnboardingService
        from app.domain.services.starter_kit_service import StarterKitService

        return OnboardingService(db, StarterKitService(db))

    @pytest.mark.parametrize("field", sorted(_WIZARD_SELECTIONS))
    def test_reset_wizard_clears_it(self, db, state_key, field):
        from app.data_access.arango import collections as col

        self._service(db).reset_wizard(_USER_KEY)

        assert _raw(db, col.ONBOARDING_STATES, state_key).get(field) is None, (
            f"the reset wizard reopens on the previous run's {field}"
        )

    def test_reset_wizard_keeps_the_identity_of_the_state(self, db, state_key):
        from app.data_access.arango import collections as col

        self._service(db).reset_wizard(_USER_KEY)

        stored = _raw(db, col.ONBOARDING_STATES, state_key)
        assert stored["user_key"] == _USER_KEY
        assert stored["completed"] is False
        assert stored["legacy_attr"] == _UNDECLARED["legacy_attr"]


# ── notifications (#1516) ────────────────────────────────────────────────────


class TestAResurfacedNotificationIsUnreadAgain:
    _PLANT_KEY = "plant-basil"

    @pytest.fixture
    def notification_key(self, db) -> str:
        from app.data_access.arango import collections as col

        meta = db.collection(col.NOTIFICATIONS).insert(
            {
                "tenant_key": _TENANT_KEY,
                "user_key": _USER_KEY,
                "notification_type": "care.watering",
                "title": "Basil",
                "body": "Giessen faellig",
                "group_key": f"care.watering:{self._PLANT_KEY}",
                "status": "delivered",
                "read_at": "2026-03-01T09:00:00+00:00",
                "acted_at": "2026-03-01T09:00:01+00:00",
                **_UNDECLARED,
            }
        )
        return str(meta["_key"])

    @pytest.mark.parametrize("field", ["read_at", "acted_at"])
    def test_reset_read_clears_it(self, db, notification_key, field):
        """#769: the follow-up occurrence recycles the row the confirmation stamped read.

        With both timestamps dropped by the merge the row stayed read, and the
        unread list and badge — which filter strictly on ``read_at == null`` —
        never showed the new occurrence.
        """
        from app.common.enums import ReminderType
        from app.data_access.arango import collections as col
        from app.data_access.arango.notification_repository import ArangoNotificationRepository
        from app.domain.services.notification_propagation_service import NotificationPropagationService

        NotificationPropagationService(ArangoNotificationRepository(db)).sync_care_notification(
            tenant_key=_TENANT_KEY,
            user_key=_USER_KEY,
            plant_key=self._PLANT_KEY,
            plant_label="Basil",
            reminder_type=ReminderType.WATERING,
            due_date=datetime.now(UTC) + timedelta(days=2),
            reset_read=True,
        )

        stored = _raw(db, col.NOTIFICATIONS, notification_key)
        assert stored.get(field) is None, f"a re-surfaced notification kept its {field} and stays out of the badge"
        assert stored["legacy_attr"] == _UNDECLARED["legacy_attr"]
