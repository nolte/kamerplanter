"""#1397 group C — the label projections anchor on the parent site, not on the empty field.

`Location.tenant_key` and `Slot.tenant_key` exist on the documents and the write
path never fills them: `POST /t/{slug}/locations` builds
``Location(**body.model_dump())`` and `LocationCreate` may not carry a tenant key
(`check_tenant_body_field.py`, #1000), and `PUT /slots/{key}` replaces the whole
slot the same way. A location is tenant-resolved through its parent **site**.

Two queries guarded their `location_name` / `slot_label` projections with
``location.tenant_key == @tenant_key``, so those labels came back ``null`` for
every location the caller owns. Not for *every* row, which is why it survived
review: migration ``v0004_backfill_tenant_key`` propagated site → locations →
slots once, so documents predating it compare true and everything created since
does not — a projection whose correctness depends on the age of the row.

**What this file is, and what it is not.** It asserts on the AQL *string*, which
cannot prove what the database answers. The proof of the answer is
`tests/integration/test_location_label_projection.py`, which builds locations with
``tenant_key: ""`` — the shape the write path produces — and asserts the label
comes back. That file needs a real ArangoDB. It was absent from CI until #1432,
where it would have self-skipped and reported green having tested nothing; since
then it runs in the required `Integration tests (ArangoDB)` job
(`.github/workflows/backend-guards.yml`, the unfiltered lane) against a service
container, and a missing database is a failure rather than a skip.

So this is the CI-visible half: it pins the *rule* — the anchor is walked, and the
empty field is not consulted — so the repair cannot be undone without a red lane,
even though only the integration tier can show the consequence. The negative
assertion carries most of the weight here: a query may mention ``@site_col`` and
still compare the wrong field.
"""

from __future__ import annotations

import re
from typing import Any

from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository


class _CapturingAql:
    def __init__(self, result: list[Any]) -> None:
        self.query: str | None = None
        self.bind_vars: dict[str, Any] | None = None
        self._result = result

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.query = query
        self.bind_vars = bind_vars or {}
        return iter(self._result)


class _CapturingDb:
    def __init__(self, result: list[Any] | None = None) -> None:
        self.aql = _CapturingAql(result or [])

    def collection(self, _name: str):  # pragma: no cover - must not be reached
        raise AssertionError("these projections must run through AQL, not raw collections")


def _strip_comments(query: str) -> str:
    """AQL without its ``//`` comments.

    Both queries explain the repair in a comment that names the old expression, so
    a bare ``"location.tenant_key" not in query`` would fail on the documentation
    of the very rule it checks.
    """
    return re.sub(r"//[^\n]*", "", query)


def _capture_in_phase_definition() -> str:
    db = _CapturingDb()
    repo = ArangoPlantInstanceRepository(db)  # type: ignore[arg-type]
    repo.list_active_in_phase_definition("tenant-A", "pd-1")
    return _strip_comments(db.aql.query or "")


def _capture_for_tenant() -> str:
    db = _CapturingDb()
    repo = ArangoPlantInstanceRepository(db)  # type: ignore[arg-type]
    repo.list_active_for_tenant("tenant-A", limit=25)
    return _strip_comments(db.aql.query or "")


class TestTheLabelGuardsDoNotConsultTheEmptyField:
    def test_the_phase_definition_list_never_compares_location_or_slot_tenant_key(self) -> None:
        query = _capture_in_phase_definition()

        assert "location.tenant_key" not in query, (
            "the label guard is back on Location.tenant_key, which the write path stores empty; "
            "anchor on the parent site instead (#1397)"
        )
        assert "slot.tenant_key" not in query, (
            "the slot label guard is back on Slot.tenant_key, which the write path stores empty (#1397)"
        )

    def test_the_tenant_list_never_compares_location_tenant_key(self) -> None:
        query = _capture_for_tenant()

        assert "location.tenant_key" not in query, "the dashboard label guard is back on Location.tenant_key (#1397)"


class TestTheLabelGuardsWalkTheSiteAnchor:
    """Presence, so 'stop checking anything' cannot pass the absence tests above.

    Dropping the guard entirely would satisfy every assertion in the class above
    and hand another tenant's location name to this caller — the opposite defect,
    and the one the integration tier's `loc-foreign` row pins.
    """

    def test_the_phase_definition_list_resolves_both_anchors(self) -> None:
        query = _capture_in_phase_definition()

        assert "DOCUMENT(@site_col, location.site_key)" in query, (
            "the location label no longer resolves its parent site (#1397)"
        )
        assert "DOCUMENT(@location_col, slot.location_key)" in query, (
            "the slot label no longer resolves its parent location (#1397)"
        )
        assert "location_site.tenant_key == @tenant_key" in query
        assert "slot_site.tenant_key == @tenant_key" in query

    def test_the_tenant_list_resolves_the_site_anchor(self) -> None:
        query = _capture_for_tenant()

        assert "DOCUMENT(@site_col, location.site_key)" in query
        assert "location_site.tenant_key == @tenant_key" in query

    def test_the_site_collection_is_bound_not_interpolated(self) -> None:
        """A `@site_col` in the text with no bind var is a query that cannot run."""
        for capture in (
            ("list_active_in_phase_definition", ArangoPlantInstanceRepository.list_active_in_phase_definition),
            ("list_active_for_tenant", ArangoPlantInstanceRepository.list_active_for_tenant),
        ):
            name, method = capture
            db = _CapturingDb()
            repo = ArangoPlantInstanceRepository(db)  # type: ignore[arg-type]
            if name == "list_active_in_phase_definition":
                method(repo, "tenant-A", "pd-1")
            else:
                method(repo, "tenant-A", 25)

            bind_vars = db.aql.bind_vars or {}
            assert bind_vars.get("site_col") == "sites", f"{name} does not bind @site_col"
            # Comments stripped first. Asserted against the raw text, this passed
            # only because neither AQL comment happens to contain the word "sites";
            # one ordinary sentence like "resolved through the sites collection"
            # would have turned it red with a message naming a defect that is not
            # there. A check that depends on the wording of a comment is not
            # checking what it says it checks.
            body = _strip_comments(db.aql.query or "").replace("@site_col", "")
            assert "sites" not in body, f"{name} interpolates the collection name instead of binding it"
