"""The declared-inventories helper of the reach audit (#1680) scoped to what the query log can see (#3090).

``scripts/reach/declared_privacy_inventories.py`` prints the collections each personal-data
inventory declares; ``observe_executing_inventory.py`` lists an inventory only when ArangoDB's
query log shows every one of them read during the real export. Two kinds of export source can
never appear there by construction — a personal-tenant source (the reach subject owns no
personal garden) and a time-series source (served by TimescaleDB) — so the helper leaves them
out, reading that from each source's own declaration.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

from app.domain.engines.data_export_engine import DataExportEngine
from tests.support.repo_scripts import load_repo_script

helper = load_repo_script("reach/declared_privacy_inventories")


def _printed() -> dict[str, list[str]]:
    out = io.StringIO()
    with redirect_stdout(out):
        assert helper.main(["--subject", "reach-subject"]) == 0
    return json.loads(out.getvalue())


def _collections(sources: list) -> set[str]:
    return {s.collection for s in sources} | {s.edge_collection for s in sources if s.edge_collection}


def test_the_export_inventory_leaves_out_exactly_the_sources_the_query_log_cannot_see() -> None:
    manifest = [s for s in DataExportEngine().build_export_manifest("reach-subject") if s.disclosure_gap is None]
    unseeable = [s for s in manifest if s.personal_tenant_scope is not None or s.time_series is not None]
    seeable = [s for s in manifest if s.personal_tenant_scope is None and s.time_series is None]
    assert unseeable, "the manifest declares personal-tenant and time-series sources; the test needs one"
    assert set(_printed()["export-manifest"]) == _collections(seeable)


def test_a_time_series_source_is_never_listed() -> None:
    manifest = DataExportEngine().build_export_manifest("reach-subject")
    only_time_series = {s.collection for s in manifest if s.time_series is not None} - _collections(
        [s for s in manifest if s.time_series is None and s.personal_tenant_scope is None]
    )
    assert only_time_series
    assert not only_time_series & set(_printed()["export-manifest"])
