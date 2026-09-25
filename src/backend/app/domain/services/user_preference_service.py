import structlog

from app.common.exceptions import DuplicateError, WriteConflictError
from app.common.log_privacy import log_subject
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.user_preference import DashboardLayout, UserPreference
from app.domain.services.dashboard_widget_catalog import WIDGET_BY_KEY
from app.domain.services.singleton_document import pick_singleton

logger = structlog.get_logger()

# REQ-045 — backend widget registry, derived from the single widget-metadata
# source (WIDGET_CATALOG) so the two backend lists cannot drift. MUST stay in
# sync with the frontend ``dashboardWidgetCatalog`` (contract test, REQ-045 §6).
KNOWN_WIDGET_KEYS: frozenset[str] = frozenset(WIDGET_BY_KEY)


def _sanitize_layout(layout: DashboardLayout) -> DashboardLayout:
    """Drop widgets with an unknown widget_key (warn-log), keep the rest.

    Deliberately tolerant (like module_visibility): the backend does not
    reject a whole layout just because one widget key does not (yet/anymore)
    exist — forward/backward compatibility across client versions.
    """
    keep: list = []
    dropped: list = []
    for widget in layout.widgets:
        (keep if widget.widget_key in KNOWN_WIDGET_KEYS else dropped).append(widget)
    if dropped:
        logger.warning(
            "dashboard_layout.unknown_widgets_dropped",
            widget_keys=[w.widget_key for w in dropped],
        )
    # Prune placements referencing orphaned instance_ids (per-breakpoint consistency).
    kept_ids = {w.instance_id for w in keep}
    pruned = {
        breakpoint_key: [p for p in places if p.instance_id in kept_ids]
        for breakpoint_key, places in layout.placements.items()
    }
    return layout.model_copy(update={"widgets": keep, "placements": pruned})


KNOWN_MODULE_KEYS: frozenset[str] = frozenset(
    {
        "dashboard",
        "plants",
        "locations",
        "settings",
        "onboarding",
        "care",
        "calendar",
        "watering",
        "tasks",
        "nutrition",
        "tanks",
        "substrates",
        "calculators",
        "ipm",
        "harvest",
        "post_harvest",
        "runs",
        "propagation",
        "master_data",
        "companion",
        "sensors",
        "automation",
        "smart_home",
        "ai",
    }
)


class UserPreferenceService:
    def __init__(self, db) -> None:
        from app.data_access.arango import collections as col

        # Service-embedded dict view: methods below wrap the raw dict into
        # UserPreference themselves, so opt into raw mode (FR-002 A3).
        self._repo = BaseArangoRepository(db, col.USER_PREFERENCES, raw=True)

    def _stored(self, user_key: str) -> UserPreference | None:
        """The user's stored preferences, or ``None`` — the read, with no side effect."""
        from app.data_access.arango import collections as col

        docs = self._repo.find_by_field("user_key", user_key)
        if not docs:
            return None
        return UserPreference(**pick_singleton(docs, collection=col.USER_PREFERENCES, user_key=user_key))

    def get_preferences(self, user_key: str) -> UserPreference:
        """Return the user's preferences, defaults included — **without persisting**.

        This used to auto-create the singleton on a cold read, which made
        ``GET /t/{slug}/user-preferences`` (and, through it,
        ``GET …/dashboard/widgets/catalog``) a write on a safe method: entries 8
        and 9 of the #1443 detector inventory, filed as #1461.

        Nothing needed the row to exist at read time. The response is identical
        either way — an unmaterialised user gets the same defaults the freshly
        created document would have carried — with one visible difference: ``key``
        is ``None`` until a write materialises the row. The row is created by
        :meth:`update_preferences`, which is where the user first states a
        preference worth storing.
        """
        stored = self._stored(user_key)
        return stored if stored is not None else UserPreference(user_key=user_key)

    def _materialise(self, user_key: str) -> UserPreference:
        """Return the stored preferences, creating the singleton if there is none.

        The auto-create that used to sit on the read path (#1461). Two concurrent
        FIRST WRITES both find the collection empty and both try to insert; the
        unique index on ``user_key`` refuses the loser. Re-read and return the
        winner's document instead of surfacing a 409 (upsert semantics).

        BOTH refusals are caught (#1458). Which one the loser gets is the server's
        decision about how far the winner had got: 1210 (DuplicateError) once the
        winner's unique-index entry is committed and visible, 1200
        (WriteConflictError) while its transaction still holds the entry. A caller
        that caught only DuplicateError was still a 500 under exactly the load the
        retry exists for — the same pairing ``care_reminder_service`` made for the
        profile+edge race (#1292).
        """
        stored = self._stored(user_key)
        if stored is not None:
            return stored
        try:
            doc = self._repo.create(UserPreference(user_key=user_key))
        except DuplicateError, WriteConflictError:
            winner = self._stored(user_key)
            if winner is None:  # pragma: no cover - the index refused us; somebody holds the row
                raise
            return winner
        return UserPreference(**doc)

    def update_preferences(self, user_key: str, updates: dict) -> UserPreference:
        mv = updates.get("module_visibility")
        if mv:
            unknown = set(mv) - KNOWN_MODULE_KEYS
            if unknown:
                logger.warning("unknown_module_visibility_keys", keys=sorted(unknown))
        # REQ-045 — sanitize a submitted layout (drop unknown widgets). An
        # explicit null resets to the experience-level default; "unset" (key
        # absent) leaves the stored layout untouched — the router uses
        # exclude_unset so this distinction survives.
        if "dashboard_layout" in updates and updates["dashboard_layout"] is not None:
            layout = DashboardLayout.model_validate(updates["dashboard_layout"])
            updates["dashboard_layout"] = _sanitize_layout(layout).model_dump()
        # The first write is what creates the row (#1461), so this resolves through
        # ``_materialise`` rather than through the — now read-only — public getter.
        pref = self._materialise(user_key)
        data = pref.model_dump()
        data.update(updates)
        # Validate the *merged* model so field-level sanitisation/coercion
        # (e.g. _drop_core_overrides, enum parsing) still applies to the
        # submitted values.
        validated = UserPreference(**data)
        # Persist only a *partial* update-doc containing exactly the keys this
        # PATCH touched, taking their sanitised values from the validated model.
        # Writing the full document back would clobber a concurrent PATCH of a
        # disjoint field (lost update, reproduced under xdist parallel load):
        # two clients both read the whole record, each re-writes its own stale
        # full snapshot, and the later writer wins for *every* field. ArangoDB's
        # partial update merges disjoint keys, so parallel PATCHes commute.
        serialized = validated.model_dump(mode="json")
        fields = {field_name: serialized[field_name] for field_name in updates}
        # Audit trail: which keys each PATCH touched (values only for the
        # level, the field most sensitive to concurrent-writer surprises).
        logger.info(
            "user_preferences_updated",
            subject=log_subject(user_key),
            keys=sorted(fields),
            experience_level=fields.get("experience_level"),
        )
        doc = self._repo.update_fields(pref.key or "", fields)
        return UserPreference(**doc)
