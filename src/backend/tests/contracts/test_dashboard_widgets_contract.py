"""Consumer-driven contract: the backend widget registry (``KNOWN_WIDGET_KEYS``)
must be exactly the widget-key set the frontend catalog offers (REQ-045 §6).

The shared contract lives at
``src/frontend/src/contracts/dashboard-widgets.json`` and is also asserted from
the frontend
(``src/frontend/src/test/contracts/dashboardWidgets.contract.test.ts``).

A drift on either side — a widget key added to the frontend catalog without a
backend registry entry, or a backend key renamed — now fails a test before
merge. Unknown keys are only *tolerated* at runtime (sanitize-and-log); this
test keeps the two catalogs deliberately in lock-step so the toleration path is
never hit by our own code.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.domain.services.dashboard_widget_catalog import WIDGET_BY_KEY
from app.domain.services.user_preference_service import KNOWN_WIDGET_KEYS

_CONTRACT_PATH = (
    Path(__file__).resolve().parents[4] / "src" / "frontend" / "src" / "contracts" / "dashboard-widgets.json"
)


def _load_contract_keys() -> set[str]:
    data = json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))
    return set(data["widget_keys"])


class TestDashboardWidgetContract:
    def test_contract_file_is_present_and_nonempty(self) -> None:
        keys = _load_contract_keys()
        assert keys, "contract must list at least one widget key"

    def test_known_widget_keys_match_contract(self) -> None:
        contract = _load_contract_keys()
        missing = contract - KNOWN_WIDGET_KEYS
        extra = KNOWN_WIDGET_KEYS - contract
        assert not missing, f"frontend offers widget(s) {sorted(missing)} the backend does not register"
        assert not extra, f"backend registers widget(s) {sorted(extra)} the frontend catalog does not offer"

    def test_widget_metadata_covers_contract(self) -> None:
        # Every contract key must also have server-side metadata for the catalog.
        contract = _load_contract_keys()
        missing = contract - set(WIDGET_BY_KEY)
        assert not missing, f"widget(s) {sorted(missing)} lack backend metadata in WIDGET_CATALOG"
