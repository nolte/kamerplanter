#!/usr/bin/env python3
"""Generate the REQ-053 acceptance matrix GP-ACC <-> test, from the tests (WP 6.1, #2445).

The matrix is never edited by hand. The acceptance criteria come from the spec
(``spec/req/REQ-053_*.md``, the ``- **GP-ACC-nnn**`` list of section 30); the tests are
scanned for the id they carry. One convention, the one the suites already use:

* the literal ``GP-ACC-nnn`` anywhere in a test file (module docstring, ``describe``/``it``
  title, comment), or
* ``gp_acc_nnn`` in a Python test-function name.

Scanned files: ``src/backend/tests/**/test_*.py`` (tier from the directory: ``unit``,
``api``, ``integration``, ``guards``), ``src/frontend/src/**/*.test.ts[x]`` (tier ``frontend``),
``tests/e2e/test_*.py`` and ``**/*.feature`` (tier ``e2e``). Fixtures, page objects and
production code that merely quote an id are not tests and are not scanned.

An id without a test fails the check unless ``spec/e2e-testcases/GP-ACC-gaps.json`` lists it
with a ``reason`` and a tracking ``issue``. That allowlist is the only way to carry an honest
gap, and the check fails again when a listed id has gained a test (remove it then).

Wave 7 (WP 7.27, #2493) adds a second matrix with the same rules: the SHOULD rows of wave 7 (GP-FR / GP-API /
GP-UX, listed in :data:`WAVE7_ROWS` from plan section 3 "Welle 7" and spec section 34) against the tests that carry
the row id. A test carries ``GP-FR-nnn`` (or ``GP-API-nnn`` / ``GP-UX-nnn``) literally; the shorthand
``GP-FR-158/159`` counts for each number. Output ``spec/e2e-testcases/GP-REQ-wave7-matrix.md``; honest gaps in
``GP-REQ-wave7-gaps.json`` - a full gap (no test at all) or, with ``"partial": true``, a row whose tests leave a
named part of it unproven (for example GP-FR-025: multi-duplicate is tested, the ``Ctrl/Cmd+D`` key is not wired).

Wave 8 (WP 8.32, #2675) adds a third matrix with the same rules for the rows of wave 8 (plan section 3 "Welle 8",
WP 8.1-8.29; spec section 34 row 8), listed in :data:`WAVE8_ROWS`. Wave 8 also carries GP-NFR rows (backfill
migration, consistency job, INP profile, import schema compatibility), so a test claims ``GP-NFR-nnn`` the same way.
Output ``spec/e2e-testcases/GP-REQ-wave8-matrix.md``; honest gaps in ``GP-REQ-wave8-gaps.json``.

Wave 9 (WP 9.17, #2757) adds a fourth matrix: the GP-FR / GP-UX / GP-NFR / GP-API rows of wave 9 (:data:`WAVE9_ROWS`,
plan section 3 "Welle 9", WP 9.1-9.16) and the UI-NFR-012 requirements wave 9 implements (:data:`WAVE9_UINFR_ROWS`,
UI-NFR-012 v2.3 section 2.3). A UI-NFR-012 id (``R-057``) is no unique string in the repo - the REQ documents have
R-ids of their own - so a test claims one only in a file that names ``UI-NFR-012`` somewhere; a range written
``R-021…R-027`` (or with ``...``/``–``/``—``) claims every number in it. The matrix adds an "E2E TC" column: the
``TC-053-nnn`` of each E2E test function (``def test_tc_053_nnn_...``) whose body names the row.
Output ``spec/e2e-testcases/GP-REQ-wave9-matrix.md``; honest gaps in ``GP-REQ-wave9-gaps.json``.

Usage: ``python3 scripts/gp_acc_matrix.py [--write | --check]`` (default ``--check``).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_GLOB = "spec/req/REQ-053_*.md"
MATRIX = ROOT / "spec/e2e-testcases/GP-ACC-matrix.md"
GAPS = ROOT / "spec/e2e-testcases/GP-ACC-gaps.json"

_SPEC_ID = re.compile(r"^- \*\*GP-ACC-(\d{3})\*\*\s*\(([^)]*)\)", re.MULTILINE)
_TEST_ID = re.compile(r"GP-ACC-(\d{3})|gp_acc_(\d{3})", re.IGNORECASE)
_SKIP_DIRS = {"node_modules", ".git", "fixtures", "__pycache__"}
_SELF = {"test_req053_acceptance_matrix.py"}

WAVE7_MATRIX = ROOT / "spec/e2e-testcases/GP-REQ-wave7-matrix.md"
WAVE7_GAPS = ROOT / "spec/e2e-testcases/GP-REQ-wave7-gaps.json"
_SPEC_ROW = re.compile(r"^\| GP-(FR|UX|API|NFR)-(\d{3}) \|([^|]*)\|", re.MULTILINE)
#: A row id with its own boundaries: ``GP-NFR-0151`` is no claim of GP-NFR-015, and the ``/ddd`` shorthand only counts
#: a three-digit number that ends there (``GP-FR-105/2026-11`` claims GP-FR-105 only).
_TEST_ROW = re.compile(r"(?<![\w-])GP-(FR|API|UX|NFR)-(\d{3})(?!\d)((?:/\d{3}(?!\d))*)")

WAVE8_MATRIX = ROOT / "spec/e2e-testcases/GP-REQ-wave8-matrix.md"
WAVE8_GAPS = ROOT / "spec/e2e-testcases/GP-REQ-wave8-gaps.json"

WAVE9_MATRIX = ROOT / "spec/e2e-testcases/GP-REQ-wave9-matrix.md"
WAVE9_GAPS = ROOT / "spec/e2e-testcases/GP-REQ-wave9-gaps.json"
UINFR_GLOB = "spec/ui-nfr/UI-NFR-012_*.md"
#: The prefix a UI-NFR-012 row carries in the wave-9 matrix and its gap file (``UI-NFR-012 R-057``).
UINFR = "UI-NFR-012"
_UINFR_ROW = re.compile(r"^\| (R-\d{3}[a-f]?) \|.*\| (MUSS|SOLL|KANN) \|[ \t]*$", re.MULTILINE)
_UINFR_RANGE = re.compile(r"(?<![\w-])R-(\d{3})\s*(?:…|\.\.\.|–|—)\s*R-(\d{3})(?![\d])")
_UINFR_ID = re.compile(r"(?<![\w-])R-(\d{3}[a-f]?)(?![\w])((?:/\d{3}(?!\d))*)")
_NAMES_UINFR = re.compile(r"(?<![\w-])UI-NFR-012(?!\d)")
_E2E_TC_FUNCTION = re.compile(r"^def test_tc_053_(\d{3})\w*\(", re.MULTILINE)
#: The end of a top-level block: the next line that starts at column 0 (``def``, ``async def``, ``class``, a
#: decorator, a constant, a comment) - a function body is indented.
_TOP_LEVEL_LINE = re.compile(r"\n(?=[^\s])")
#: The end of a function signature: the ``:`` that closes ``def …(…) -> T:`` at the end of a line.
_SIGNATURE_END = re.compile(r"\)[^\n:]*:[ \t]*(?:#[^\n]*)?\n")
#: Where the scope of a ``UI-NFR-012`` prefix ends: another document prefix (``REQ-053``, ``NFR-011``, another
#: UI-NFR, a ``GP-``/``SR-`` id), a blank (comment) line, the end of a docstring or block comment, or the end of
#: a sentence. Only the R-ids between the prefix and that end belong to UI-NFR-012.
_UINFR_SCOPE_END = re.compile(
    r"(?<![\w-])(?:REQ-\d{3}|(?<!UI-)NFR-\d{3}|UI-NFR-(?!012(?!\d))\d{3}|GP-[A-Z]+-\d{3}|SR-\d{3})"
    r"|\n[ \t]*(?:\*|#|//)?[ \t]*\n|\"\"\"|\*/|\.(?=\s)"
)
#: The widest range ``R-aaa…R-bbb`` that is read as a range; a wider or reversed one is reported, not dropped.
_UINFR_RANGE_MAX = 30

WAVE10_MATRIX = ROOT / "spec/e2e-testcases/GP-REQ-wave10-matrix.md"
WAVE10_GAPS = ROOT / "spec/e2e-testcases/GP-REQ-wave10-gaps.json"
#: The prefix a workspace acceptance criterion carries in the wave-10 matrix (``§17.3 AC-7``).
AC = "§17.3"
#: The prefix a domain finding of Anhang A 60-63 carries in the wave-10 matrix (``REQ-053 W-015``).
WREQ = "REQ-053"
#: An acceptance criterion row of the workspace table in section 17.3 (``| AC-7 | ... |``).
_AC_ROW = re.compile(r"^\| AC-(\d{1,2}) \|", re.MULTILINE)
#: An ``AC-n`` claim; ``AC-15 part`` counts, ``AC-150`` or ``XAC-1`` does not.
_AC_ID = re.compile(r"(?<![\w-])AC-(\d{1,2})(?!\d)")
#: A file claims workspace criteria only when it names section 17.3 or one of the rows they accept (GP-UX-063-070):
#: ``AC-n`` is no unique string in the repo (other specs number their criteria the same way).
_NAMES_WORKSPACE = re.compile(r"§\s?17\.3(?!\d)|(?<![\w-])GP-UX-0(?:6[3-9]|70)(?!\d)")
#: A review finding of REQ-053 (``W-015``, also ``W-016.6`` for the sub-point of W-016).
_W_ID = re.compile(r"(?<![\w-])W-(\d{3})(?:\.\d+)?(?!\d)")
#: A file claims a W-id only when it names REQ-053 (the W-ids are the agrobiology findings of this spec).
_NAMES_REQ053 = re.compile(r"(?<![\w-])REQ-053(?!\d)")


@cache
def _read(path: Path) -> str:
    """One read per file and run: the scans of all four matrices share it (a test that writes a probe uses a
    fresh ``tmp_path``, so a cached file is never rewritten under the same path)."""
    return path.read_text(encoding="utf-8", errors="replace")

#: The SHOULD rows of wave 7 (plan section 3 "Welle 7", WP 7.1-7.24; spec section 34 row 7), with the part a row
#: contributes when only part of it is SHOULD. Not here, with the plan's reason: GP-FR-161-168 (wave 8 per section
#: 34), GP-FR-078/115/116/118 (COULD), GP-FR-086/087 (suggestions and template tasks hang on ADR-008 phase 2 / wave 8).
WAVE7_ROWS: dict[str, str] = {
    "GP-FR-012": "SHOULD part: snap to edges/corners of neighbouring objects",
    "GP-FR-025": "SHOULD part: multi-duplicate (count, direction, spacing, naming scheme)",
    "GP-FR-029": "align / distribute a multi-selection",
    "GP-FR-031": "SHOULD part: layer switches for zones and 'last watered'",
    "GP-FR-033": "background underlay with two-point calibration",
    "GP-FR-043": "height of raised bed / planter, pre-filled from the template",
    "GP-FR-044": "bed templates (tenant + system)",
    "GP-FR-045": "standard sizes as quick pick",
    "GP-FR-110": "irrigation zones: CRUD, assign beds, zone outline on the plan",
    "GP-FR-111": "water source object with capacity and last refill",
    "GP-FR-112": "last watering per zone and bed",
    "GP-FR-113": "zone demand from REQ-037 (net litres, gross with efficiency)",
    "GP-FR-114": "zone consumption (logged + actuator runtime x flow rate)",
    "GP-FR-117": "watering round of a zone (allocated total)",
    "GP-FR-119": "conflict hint zone type vs bed irrigation system",
    "GP-FR-148": "snapshots before replace, list and restore",
    "GP-FR-158": "sun profile (sun window chips)",
    "GP-FR-159": "foliage shade in summer",
    "GP-FR-169": "map layers sun / moisture-drainage / frost risk",
    "GP-FR-171": "new season from the previous year",
    "GP-FR-172": "partial export and import target",
    "GP-UX-004": "auto-save option, paused on conflict",
    "GP-UX-014": "mini-map",
    "GP-UX-031": "layer 'last watered'",
    "GP-UX-051": "import wizard (delivered with WP 5.3, listed in section 34 wave 7)",
    "GP-UX-057": "field-mode bed sheet with sun / moisture chips",
    "GP-UX-061": "plant-state layer and 'needs attention' filter",
    "GP-API-050": "irrigation zone CRUD",
    "GP-API-051": "replace the beds of a zone",
    "GP-API-052": "zone status",
    "GP-API-053": "log a watering round (allocation by_area | equal)",
    "GP-API-057": "new season from the previous year",
    "GP-API-058": "list plan snapshots",
    "GP-API-059": "restore a plan snapshot",
    "GP-API-060": "set / remove the plan underlay",
    "GP-API-061": "bed template catalogue CRUD",
    "GP-API-062": "place a bed from a template",
}


#: The rows of wave 8, with the part a row contributes when only part of it is wave 8. The rule: a row is here when a
#: work package of plan section 3 "Welle 8" (WP 8.1-8.29) names it as its deliverable - whatever its priority; that is
#: why the COULD row GP-FR-168 (WP 8.22/8.24) is here. Not here, because no wave-8 package delivers them: GP-FR-131/132
#: (delivered in wave 3), GP-FR-157-160 and 169 (wave 7), GP-FR-144, 165, 167, 173, 176 (wave 9 per section 34), the
#: COULD rows GP-FR-108/126/127/136 and GP-FR-087/091 (named by no wave-8 package).
WAVE8_ROWS: dict[str, str] = {
    "GP-FR-051": "bed photos with cover photo, gallery tab, field-mode photo (WP 8.18, 8.19)",
    "GP-FR-086": "suggestions section with accept / dismiss (WP 8.17; no producer, E-02)",
    "GP-FR-104": "care history of a bed as CSV, hardened (WP 8.4)",
    "GP-FR-105": "M4 backfill and the daily consistency job (WP 8.1, 8.2)",
    "GP-FR-106": "care confirmations also write a care event (WP 8.3)",
    "GP-FR-122": "soil analysis as an event, history chart per method (WP 8.7, 8.8)",
    "GP-FR-123": "area dosing: rate from the product sheet, total from the bed area (WP 8.9)",
    "GP-FR-124": "soil amendment materials as codes (WP 8.9)",
    "GP-FR-125": "nutrient hint per bed, never a number (WP 8.10)",
    "GP-FR-133": "follow-up crop recommendation, order only (WP 8.14)",
    "GP-FR-134": "companion-planting layer (WP 8.15, 8.16)",
    "GP-FR-135": "rotation matrix per site (WP 8.12, 8.13)",
    "GP-FR-137": "wave-8 part: the per-bed rotation switch in the soil tab (WP 8.14)",
    "GP-FR-145": "bed list as CSV (WP 8.25)",
    "GP-FR-161": "site_fit with frost, wind and drainage (WP 8.21)",
    "GP-FR-162": "frost risk per bed in the early warning and the plant state (WP 8.20, 8.22)",
    "GP-FR-163": "wind exposure entered by hand (WP 8.22)",
    "GP-FR-164": "sun class thresholds as site configuration (WP 8.24)",
    "GP-FR-166": "reach hint bed.reach_too_wide (WP 8.23)",
    "GP-FR-168": "slope / aspect per bed, orientation derived from the aspect (WP 8.22, 8.24)",
    "GP-FR-174": "CSV bed list import with dry-run report (WP 8.26, 8.27)",
    "GP-FR-175": "column selection of the bed list CSV, assignment opt-in (WP 8.25)",
    "GP-UX-057": "wave-8 part: field-mode chips moist / normal / dry and windy (WP 8.22)",
    "GP-NFR-015": "wave-8 part: migration M4_care_events_backfill with dry-run report (WP 8.1)",
    "GP-NFR-016": "wave-8 part: Celery beat task care_events_consistency (WP 8.2)",
    "GP-NFR-063": "consistency job reports run time and hits, warns above 100 (WP 8.2)",
    "GP-NFR-071": "INP measurement profile (WP 8.29)",
    "GP-NFR-072": "import migrates the last two schema versions (WP 8.28)",
    "GP-API-034": "wave-8 part: format=csv on the care-event list (WP 8.4)",
    "GP-API-040": "accept / dismiss a suggested task (WP 8.17)",
    "GP-API-063": "rotation matrix of a site (WP 8.12)",
    "GP-API-064": "follow-up crop recommendation of a bed (WP 8.14)",
    "GP-API-065": "companion edges of a bed (WP 8.15)",
    "GP-API-066": "soil analysis series of a bed (WP 8.7)",
    "GP-API-067": "bed photos: list, link, cover, remove (WP 8.18)",
    "GP-API-068": "bed list as CSV with column selection (WP 8.25)",
    "GP-API-069": "CSV bed list import (WP 8.26)",
}


#: The REQ-053 rows of wave 9, with the part a row contributes when only part of it is wave 9. The rule of wave 8: a
#: row is here when a work package of plan section 3 "Welle 9" (WP 9.1-9.16) names it as its deliverable. Not here,
#: because no wave-9 package delivers them: Anhang A 60-63 (operator question 1 of #2759, own strand), GP-FR-018/146
#: (GeoJSON, WON'T per E-06), the indoor rows GP-FR-180-183 (wave 10). The rain-skipped route of WP 9.13 has no
#: GP-API row of its own (it is GP-FR-117); it is claimed through GP-FR-117.
WAVE9_ROWS: dict[str, str] = {
    "GP-UX-024": "offline read of plan, site list, bed summary and bed sheet; buffer for done / note / photo (WP 9.2, 9.4)",
    "GP-FR-025": "wave-9 part: `Ctrl/Cmd+D` duplicate through one handler, menu entry names the key (WP 9.14)",
    "GP-FR-111": "wave-9 part: water source fields in the properties panel (WP 9.14)",
    "GP-FR-117": "wave-9 part: 'Regen - übersprungen' and `by_demand` (WP 9.13)",
    "GP-FR-144": "PNG export from the SVG in 1x / 2x / 4x, watermark off by default (WP 9.8)",
    "GP-FR-165": "site flags root_competition / allelopathy_risk as a choice, no calculation (WP 9.11)",
    "GP-FR-167": "nearest_water_source_m in summary, bed list and CSV (WP 9.12)",
    "GP-FR-173": "bed template exchange as JSON without tenant keys (WP 9.9)",
    "GP-FR-176": "parcel list page in the PDF, assignment only with opt-in (WP 9.10)",
    "GP-NFR-003": "wave-9 part: the Konva renderer as its own lazy chunk, budget 200 KB gzip (WP 9.7)",
    "GP-NFR-033": "wave-9 part: drag frame-time measurement (D-01) and the Konva switch at 3 000 objects (WP 9.6, 9.7)",
    "GP-NFR-034": "wave-9 part: zoom / pan frame-time measurement (WP 9.6)",
    "GP-API-007": "wave-9 part: `parcel_list` with `include_assignment` opt-in (WP 9.10)",
    "GP-API-053": "wave-9 part: allocation `by_demand` (WP 9.13)",
    "GP-API-070": "export a bed template (WP 9.9)",
    "GP-API-071": "import a bed template with dry run (WP 9.9)",
}

#: The UI-NFR-012 requirements wave 9 implements (UI-NFR-012 v2.3 section 2.3: phase 1 plus the garden-plan buffer),
#: keyed ``UI-NFR-012 R-nnn``. Not here, with the reason of section 2.3 / REQ-053 section 32.6: R-003-R-006 (start URL
#: per device, install UI, push is older than wave 9; operator question 6), R-015 in full and R-020a-f (the buffer
#: carries done / note / photo only, R-058), R-029-R-031 (version stamps and the side-by-side dialog), R-034-R-042
#: (indicator details, offline gating of the whole app), R-046/R-047 (per-photo progress, 200 MB), R-048-R-051 and
#: R-049a/b (token persistence, question 7), R-053 (generic interceptor, replaced by R-058), R-054.
WAVE9_UINFR_ROWS: dict[str, str] = {
    f"{UINFR} R-001": "installable: manifest link and service worker (no install-prompt UI, #2759 question 6)",
    f"{UINFR} R-002": "manifest fields",
    f"{UINFR} R-007": "service worker registered and controlling",
    f"{UINFR} R-008": "Cache-First for static assets",
    f"{UINFR} R-009": "Network-First for the allowlisted API reads",
    f"{UINFR} R-010": "precache of the app shell",
    f"{UINFR} R-011": "vite-plugin-pwa (Workbox, injectManifest, one worker at /sw.js)",
    f"{UINFR} R-012": "API cache TTL 15 min (service worker and IndexedDB)",
    f"{UINFR} R-013": "API cache cap 50 MB",
    f"{UINFR} R-014": "update banner, no automatic skipWaiting",
    f"{UINFR} R-016": "offline entries in IndexedDB",
    f"{UINFR} R-017": "entry metadata: capture time, status, user, tenant",
    f"{UINFR} R-018": "entries survive a restart",
    f"{UINFR} R-019": "cap of 500 entries per user",
    f"{UINFR} R-020": "wave-9 part: site list and plan readable offline",
    f"{UINFR} R-021": "automatic sync on reconnect",
    f"{UINFR} R-022": "Background Sync where available, else on start / focus",
    f"{UINFR} R-023": "FIFO",
    f"{UINFR} R-024": "sync progress",
    f"{UINFR} R-025": "result snackbar",
    f"{UINFR} R-026": "exponential backoff 1 s to 60 s",
    f"{UINFR} R-027": "`failed` after 5 attempts, retry",
    f"{UINFR} R-028": "conflict from the server codes of WP 9.3 (409 / 404)",
    f"{UINFR} R-032": "simplified conflict dialog keep / discard",
    f"{UINFR} R-033": "connectivity indicator in the app shell",
    f"{UINFR} R-043": "photo as a blob in IndexedDB",
    f"{UINFR} R-044": "photo re-encoded on the device (1920 px, JPEG 80)",
    f"{UINFR} R-045": "photos uploaded one after another",
    f"{UINFR} R-052": "offlineSlice",
    f"{UINFR} R-055": "namespace user_key + tenant_key, no API data in localStorage",
    f"{UINFR} R-056": "clearing on logout / tenant switch / kill switch; buffer rules (b)-(d)",
    f"{UINFR} R-057": "read allowlist, no-store honoured",
    f"{UINFR} R-058": "write allowlist done / note / photo, idempotent replay",
    f"{UINFR} R-059": "delivery of /sw.js and manifest no-store, CSP, kill switch",
    f"{UINFR} R-060": "data on the device: retention 365 / 90 days, photo re-encoding",
}


#: The REQ-053 rows of wave 10, with the part a row contributes when only part of it is wave 10. The rule of waves 8
#: and 9: a row is here when a work package of plan section 3 "Welle 10" (WP 10.1-10.12) names it as its deliverable.
#: Not here, with the reason: GP-UX-001 (MUST of wave 2; since REQ-053 v1.19 it lists only the tools that exist, the others
#: are GP-UX-071, #2913; AC-2 below measures the list), GP-UX-005 / GP-UX-052 / GP-NFR-023 / GP-NFR-025 (older rows whose place moved with
#: section 17.3; their behaviour is unchanged and tested in their own wave), PPFD from ``lamp`` / ``lighting`` (no
#: calculation by the spec), the COULD rows without a wave (residual issues of WP 10.15).
WAVE10_ROWS: dict[str, str] = {
    "GP-UX-063": "one header bar, overflow order, below md only back / status / save / overflow (WP 10.3, 10.5)",
    "GP-UX-064": "tabs Plan / Liste / Beete with `?tab=`, deep link, Back, row opens the plan (WP 10.2)",
    "GP-UX-065": "a tab switch keeps the editor state and asks nothing (WP 10.2)",
    "GP-UX-066": "vertical tool rail with a selection group only while something is selected (WP 10.4)",
    "GP-UX-067": "canvas at viewport height, zoom / scale / mini-map as overlays (WP 10.3)",
    "GP-UX-068": "side panel tabs Eigenschaften / Ansicht / Ebenen / Zonen, no reserved width, state rule (WP 10.5)",
    "GP-UX-069": "one component tree: docked from md up, bottom sheet and TouchBar below md (WP 10.3-10.5, #2885)",
    "GP-UX-070": "testids stay, new ones registered in UI-NFR-022 (WP 10.2-10.5)",
    "GP-FR-180": "properties of window / door / furniture / lamp (and trellis, off_site), object legend (WP 10.6)",
    "GP-FR-181": "window orientation suggests the sun profile of nearby locations, never applied unasked (WP 10.7)",
    "GP-FR-182": "indoor plan: site type in the DTO, empty state, outdoor conditions hidden, 5 cm grid (WP 10.8)",
    "GP-FR-183": "planting spots: tents and shelves by `supports_layout`, tab and list named 'Pflanzplätze' (WP 10.8)",
    "GP-UX-049": "wave-10 part: the indoor empty state 'Zeichne die Umrisse deiner Wohnung …' (WP 10.8)",
}

#: The acceptance criteria of the editor workspace (REQ-053 section 17.3, AC-1-AC-17), keyed ``§17.3 AC-n``. Not here:
#: AC-11 ("REQ-053 describes the layout before it is built") - the spec itself is its evidence (v1.16, WP 10.1), no
#: test can claim it.
WAVE10_AC_ROWS: dict[str, str] = {
    f"{AC} AC-1": "1366 x 768: canvas >= 60 % of the viewport height, no control row wraps",
    f"{AC} AC-2": "1024 x 768: every editor function reachable without horizontal scrolling",
    f"{AC} AC-3": "exactly one editor header bar, no actions in the route header, vertical tool rail",
    f"{AC} AC-4": "rotate / align / delete only with a selection, 'save as template' only with one bed",
    f"{AC} AC-5": "no reserved panel width; switch with aria-expanded / aria-controls; WAI-ARIA tabs",
    f"{AC} AC-6": "layer switches with visible text in the tab 'Ebenen', with the legend",
    f"{AC} AC-7": "bed list as tab 'Beete', tab state in the URL, a row opens the plan",
    f"{AC} AC-8": "no unsaved-changes dialog on a tab switch, changes kept",
    f"{AC} AC-9": "below md TouchBar and bottom sheet, coarse pointer TouchBar everywhere, targets >= 48 px",
    f"{AC} AC-10": "existing data-testid kept or migrated with the page objects",
    f"{AC} AC-12": "no or unknown `tab` shows 'Plan'; no tab bar in field mode",
    f"{AC} AC-13": "tab 'Beete' shows the saved state; indoor 'Pflanzplätze' with `tab=beds`",
    f"{AC} AC-14": "zoom, scale bar and mini-map inside the canvas, no layout height",
    f"{AC} AC-15": "390 x 844: header with back / status / save / overflow only, entries >= 48 px with text",
    f"{AC} AC-16": "selection and viewport unchanged after Plan -> Beete -> Plan",
    f"{AC} AC-17": "panel state rule (selection opens, deselection closes only what it opened)",
}

#: The domain remainders of Anhang A 60-63 that wave 10 delivers (§32.6 item 1), keyed by the review finding the
#: spec carries for them (``REQ-053 W-015``). Not here: W-006 (the TaskCategory values, delivered in wave 4; WP 10.12
#: only closed the feeding-event part, W-007).
WAVE10_DOMAIN_ROWS: dict[str, str] = {
    f"{WREQ} W-015": "sown state, thinning creates plants, replant on a failed slot (Anhang A 60, WP 10.9)",
    f"{WREQ} W-007": "care-log soil amendment writes the feeding event of task completion (Anhang A 61, WP 10.12)",
    f"{WREQ} W-005": "trellis offered in the planting dialog when the species needs support (Anhang A 62, WP 10.10)",
    f"{WREQ} W-008": "tasks on compost / water source / storage from the properties panel (Anhang A 62, WP 10.10)",
    f"{WREQ} W-016": (
        "tent rules: supports_layout, adjacency factor, lighting, photoperiod hint, pot volume"
        " (Anhang A 63, WP 10.8, 10.11)"
    ),
}


def spec_ids() -> dict[str, str]:
    """``{id: level}`` for every acceptance criterion of the spec (``I``/``E``/``U`` ...)."""
    (spec,) = sorted(ROOT.glob(SPEC_GLOB))
    return {
        m.group(1): m.group(2).split(",")[0].strip()
        for m in _SPEC_ID.finditer(_read(spec))
    }


def _tier(rel: Path) -> str | None:
    parts, name = rel.parts, rel.name
    if (
        parts[:3] == ("src", "backend", "tests")
        and re.fullmatch(r"test_.*\.py", name)
        and name not in _SELF
    ):
        return next(
            (t for t in ("guards", "unit", "api", "integration") if t in parts[3:-1]),
            "backend",
        )
    if parts[:3] == ("src", "frontend", "src") and re.search(r"\.test\.tsx?$", name):
        return "frontend"
    if parts[:2] == ("tests", "e2e") and re.fullmatch(r"test_.*\.py", name):
        return "e2e"
    if parts[:1] in {("tests",), ("spec",)} and name.endswith(".feature"):
        return "e2e"
    return None


def scan() -> dict[str, dict[str, set[str]]]:
    """``{id: {tier: {file, ...}}}`` read from the tests."""
    found: dict[str, dict[str, set[str]]] = {}
    for base in (
        "src/backend/tests",
        "src/frontend/src",
        "tests/e2e",
        "spec/e2e-testcases",
    ):
        for path in sorted((ROOT / base).rglob("*")):
            rel = path.relative_to(ROOT)
            if not path.is_file() or _SKIP_DIRS & set(rel.parts[:-1]):
                continue
            tier = _tier(rel)
            if tier is None:
                continue
            for match in _TEST_ID.finditer(
                _read(path)
            ):
                number = match.group(1) or match.group(2)
                found.setdefault(number, {}).setdefault(tier, set()).add(rel.as_posix())
    return found


def load_gaps() -> dict[str, dict[str, str]]:
    return json.loads(GAPS.read_text(encoding="utf-8")) if GAPS.exists() else {}


def render(
    ids: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, str]],
) -> str:
    lines = [
        "# REQ-053 acceptance matrix GP-ACC <-> test",
        "",
        "<!-- GENERATED by scripts/gp_acc_matrix.py --write from the tests - do not edit by hand. -->",
        "",
        "Source of the ids: `spec/req/REQ-053_*.md` section 30. Source of the tests: the id (`GP-ACC-nnn`, or",
        "`gp_acc_nnn` in a Python test name) in a test file; see `scripts/gp_acc_matrix.py`. A reference proves",
        "that a test claims the criterion; whether it proves it completely stays a review question.",
        "Honest gaps (no test yet) are listed in `GP-ACC-gaps.json` with a reason and an issue.",
        "",
    ]
    covered = [i for i in ids if i in found]
    gap_ids = [i for i in ids if i not in found]
    lines += [
        f"**{len(covered)} of {len(ids)} criteria covered, {len(gap_ids)} listed as gap.**",
        "",
    ]
    lines += ["| GP-ACC | Level | Tiers | Tests |", "|---|---|---|---|"]
    for number, level in ids.items():
        tiers = found.get(number, {})
        if tiers:
            tier_cell = ", ".join(sorted(tiers))
            files = "<br>".join(
                f"`{f}`" for t in sorted(tiers) for f in sorted(tiers[t])
            )
        else:
            gap = gaps.get(number, {})
            tier_cell = "**GAP**"
            files = f"{gap.get('reason', 'no test')} (#{gap.get('issue', '?')})"
        lines.append(f"| GP-ACC-{number} | {level} | {tier_cell} | {files} |")
    return "\n".join(lines) + "\n"


def problems(
    ids: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, str]],
) -> list[str]:
    out = [
        f"GP-ACC-{i}: no test references it and it is not in GP-ACC-gaps.json"
        for i in ids
        if i not in found and i not in gaps
    ]
    out += [
        f"GP-ACC-{i}: in GP-ACC-gaps.json but a test now covers it - remove the entry"
        for i in gaps
        if i in found
    ]
    out += [
        f"GP-ACC-{i}: in GP-ACC-gaps.json but not in the spec"
        for i in gaps
        if i not in ids
    ]
    out += [
        f"GP-ACC-{i}: a gap entry needs a non-empty reason and an issue number"
        for i, g in gaps.items()
        if not (g.get("reason") and g.get("issue"))
    ]
    out += [
        f"GP-ACC-{i}: referenced by a test but not in the spec"
        for i in found
        if i not in ids
    ]
    return out


def spec_rows() -> dict[str, str]:
    """``{row id: priority}`` for every GP-FR / GP-UX / GP-API / GP-NFR table row (``API`` for the API rows)."""
    (spec,) = sorted(ROOT.glob(SPEC_GLOB))
    rows: dict[str, str] = {}
    for match in _SPEC_ROW.finditer(_read(spec)):
        kind, number, cell = match.groups()
        row = f"GP-{kind}-{number}"
        if row not in rows:
            rows[row] = "API" if kind == "API" else cell.strip().split(" ")[0]
    return rows


def _test_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for base in (
        "src/backend/tests",
        "src/frontend/src",
        "tests/e2e",
        "spec/e2e-testcases",
    ):
        for path in sorted((ROOT / base).rglob("*")):
            rel = path.relative_to(ROOT)
            if not path.is_file() or _SKIP_DIRS & set(rel.parts[:-1]):
                continue
            tier = _tier(rel)
            if tier is not None:
                files.append((rel, tier))
    return files


def scan_rows() -> dict[str, dict[str, set[str]]]:
    """``{row id: {tier: {file, ...}}}`` - the GP-FR / GP-API / GP-UX / GP-NFR ids of the tests (``a/b`` expanded)."""
    found: dict[str, dict[str, set[str]]] = {}
    for rel, tier in _test_files():
        text = _read(ROOT / rel)
        for match in _TEST_ROW.finditer(text):
            kind, first, rest = match.groups()
            for number in [first, *filter(None, rest.split("/"))]:
                found.setdefault(f"GP-{kind}-{number}", {}).setdefault(tier, set()).add(
                    rel.as_posix()
                )
    return found


def _load_gaps(path: Path) -> dict[str, dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def load_wave7_gaps() -> dict[str, dict[str, object]]:
    return _load_gaps(WAVE7_GAPS)


def load_wave8_gaps() -> dict[str, dict[str, object]]:
    return _load_gaps(WAVE8_GAPS)


def _render_wave(
    header: list[str],
    wave: str,
    wave_rows: dict[str, str],
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, object]],
    tcs: dict[str, set[str]] | None = None,
) -> str:
    lines = list(header)
    covered = [r for r in wave_rows if r in found]
    partial = [r for r in covered if gaps.get(r, {}).get("partial")]
    uncovered = [r for r in wave_rows if r not in found]
    lines += [
        (
            f"**{len(covered)} of {len(wave_rows)} wave-{wave} rows have a test, {len(partial)} of them with a partial"
            f" gap; {len(uncovered)} without a test.**"
        ),
        "",
    ]
    if tcs is None:
        lines += ["| Row | Prio | Scope | Tiers | Tests |", "|---|---|---|---|---|"]
    else:
        lines += ["| Row | Prio | Scope | Tiers | E2E TC | Tests |", "|---|---|---|---|---|---|"]
    for row, scope in wave_rows.items():
        tiers = found.get(row, {})
        gap = gaps.get(row, {})
        if tiers:
            tier_cell = ", ".join(sorted(tiers))
            files = "<br>".join(
                f"`{f}`" for t in sorted(tiers) for f in sorted(tiers[t])
            )
            if gap.get("partial"):
                tier_cell += " (**partial**)"
                files += (
                    f"<br>**Partial gap:** {gap.get('reason')} (#{gap.get('issue')})"
                )
        else:
            tier_cell = "**GAP**"
            files = f"{gap.get('reason', 'no test')} (#{gap.get('issue', '?')})"
        if tcs is None:
            lines.append(
                f"| {row} | {rows.get(row, '?')} | {scope} | {tier_cell} | {files} |"
            )
        else:
            tc_cell = ", ".join(f"TC-053-{n}" for n in sorted(tcs.get(row, set()))) or "-"
            lines.append(
                f"| {row} | {rows.get(row, '?')} | {scope} | {tier_cell} | {tc_cell} | {files} |"
            )
    return "\n".join(lines) + "\n"


def render_wave7(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, object]],
) -> str:
    header = [
        "# REQ-053 wave 7 requirement matrix GP-FR / GP-API / GP-UX (SHOULD) <-> test",
        "",
        "<!-- GENERATED by scripts/gp_acc_matrix.py --write from the tests - do not edit by hand. -->",
        "",
        "The rows are the SHOULD rows of wave 7 (`WAVE7_ROWS` in `scripts/gp_acc_matrix.py`: plan section 3",
        '"Welle 7", spec section 34); the priority is read from the spec table. A test claims a row by carrying',
        "its id (`GP-FR-117`, or the shorthand `GP-FR-112/117`). **Limit of the method:** a row counts as covered",
        "when a test file names its id; that is a claim, not proof the test exercises the row - whether it does",
        "stays a review question. Honest gaps are listed in",
        "`GP-REQ-wave7-gaps.json` with a reason and an issue: **GAP** (no test) or **partial** (the tests leave",
        "the named part unproven).",
        "",
    ]
    return _render_wave(header, "7", WAVE7_ROWS, rows, found, gaps)


def render_wave8(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, object]],
) -> str:
    header = [
        "# REQ-053 wave 8 requirement matrix GP-FR / GP-API / GP-UX / GP-NFR <-> test",
        "",
        "<!-- GENERATED by scripts/gp_acc_matrix.py --write from the tests - do not edit by hand. -->",
        "",
        "The rows are the rows of wave 8 (`WAVE8_ROWS` in `scripts/gp_acc_matrix.py`: plan section 3",
        '"Welle 8", WP 8.1-8.29, spec section 34); the priority is read from the spec table (`API` for an API row).',
        "A test claims a row by carrying its id (`GP-FR-135`, `GP-NFR-063`, or the shorthand `GP-FR-145/175`).",
        "**Limit of the method:** a row counts as covered when a test file names its id; that is a claim, not proof",
        "the test exercises the row - whether it does stays a review question.",
        "Honest gaps are listed in `GP-REQ-wave8-gaps.json` with a reason and an issue: **GAP** (no test) or",
        "**partial** (the tests leave the named part unproven).",
        "",
    ]
    return _render_wave(header, "8", WAVE8_ROWS, rows, found, gaps)


def _wave_problems(
    wave: str,
    wave_rows: dict[str, str],
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, object]],
) -> list[str]:
    gaps_file = f"GP-REQ-wave{wave}-gaps.json"
    out = [
        (
            f"{r}: listed in WAVE{wave}_UINFR_ROWS but not a requirement of UI-NFR-012"
            if r.startswith(f"{UINFR} ")
            else f"{r}: listed in WAVE{wave}_ROWS but not a row of the spec"
        )
        for r in wave_rows
        if r not in rows
    ]
    out += [
        f"{r}: no test references it and it is not in {gaps_file}"
        for r in wave_rows
        if r not in found and r not in gaps
    ]
    out += [
        f"{r}: a full gap in {gaps_file} but a test now covers it - remove it or mark it partial"
        for r, g in gaps.items()
        if r in found and not g.get("partial")
    ]
    out += [
        f"{r}: marked partial in {gaps_file} but no test references it - it is a full gap"
        for r, g in gaps.items()
        if g.get("partial") and r not in found
    ]
    out += [
        f"{r}: in {gaps_file} but not a wave-{wave} row"
        for r in gaps
        if r not in wave_rows
    ]
    out += [
        f"{r}: a gap entry needs a non-empty reason and an issue number"
        for r, g in gaps.items()
        if not (g.get("reason") and g.get("issue"))
    ]
    return out


def wave7_problems(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, object]],
) -> list[str]:
    return _wave_problems("7", WAVE7_ROWS, rows, found, gaps)


def wave8_problems(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, object]],
) -> list[str]:
    return _wave_problems("8", WAVE8_ROWS, rows, found, gaps)


def uinfr_rows() -> dict[str, str]:
    """``{"UI-NFR-012 R-nnn": priority}`` for every requirement row of UI-NFR-012 (``MUSS`` / ``SOLL`` / ``KANN``)."""
    (spec,) = sorted(ROOT.glob(UINFR_GLOB))
    rows: dict[str, str] = {}
    for match in _UINFR_ROW.finditer(_read(spec)):
        rows.setdefault(f"{UINFR} {match.group(1)}", match.group(2))
    return rows


def _uinfr_segments(text: str) -> list[str]:
    """The text after each ``UI-NFR-012`` up to the end of its scope (:data:`_UINFR_SCOPE_END`)."""
    segments: list[str] = []
    for match in _NAMES_UINFR.finditer(text):
        end = _UINFR_SCOPE_END.search(text, match.end())
        segments.append(text[match.end() : end.start() if end else len(text)])
    return segments


def uinfr_claims(text: str) -> tuple[set[str], list[str]]:
    """The UI-NFR-012 ids a text claims, and the ranges it could not read.

    An ``R-nnn`` counts only inside the scope of a ``UI-NFR-012`` prefix (same sentence, before another document
    prefix such as ``REQ-053 R-…``): single ids, the ``/nnn`` shorthand and ranges ``R-021…R-027``. A range wider
    than :data:`_UINFR_RANGE_MAX` or reversed is returned as a problem.
    """
    ids: set[str] = set()
    bad: list[str] = []
    for segment in _uinfr_segments(text):
        for match in _UINFR_RANGE.finditer(segment):
            first, last = int(match.group(1)), int(match.group(2))
            if first <= last <= first + _UINFR_RANGE_MAX:
                ids.update(f"{UINFR} R-{n:03d}" for n in range(first, last + 1))
            else:
                bad.append(match.group(0))
        # The ends of a range are read with the range (an unreadable range claims nothing).
        segment = _UINFR_RANGE.sub(" ", segment)
        for match in _UINFR_ID.finditer(segment):
            first, rest = match.groups()
            ids.update(f"{UINFR} R-{n}" for n in [first, *filter(None, rest.split("/"))])
    return ids, bad


def uinfr_ids(text: str) -> set[str]:
    """The UI-NFR-012 ids a text claims (see :func:`uinfr_claims`)."""
    return uinfr_claims(text)[0]


def uinfr_range_problems() -> list[str]:
    """Every range a test writes that is no readable UI-NFR-012 range (reversed, or wider than the limit)."""
    out: list[str] = []
    for rel, _tier_name in _test_files():
        for bad in uinfr_claims(_read(ROOT / rel))[1]:
            out.append(
                f"{rel.as_posix()}: UI-NFR-012 range {bad!r} is reversed or wider than {_UINFR_RANGE_MAX} - "
                "name the ids instead"
            )
    return out


def stray_uinfr(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
) -> list[str]:
    """UI-NFR-012 ids a test claims that are no requirement of UI-NFR-012 (a typo or a retired id)."""
    return [
        f"{r}: referenced by {', '.join(sorted(f for files in found[r].values() for f in files))}"
        " but not a requirement of UI-NFR-012"
        for r in sorted(found)
        if r.startswith(f"{UINFR} ") and r not in rows
    ]


def scan_uinfr_rows() -> dict[str, dict[str, set[str]]]:
    """``{"UI-NFR-012 R-nnn": {tier: {file, ...}}}`` - the UI-NFR-012 ids the tests claim."""
    found: dict[str, dict[str, set[str]]] = {}
    for rel, tier in _test_files():
        for row in uinfr_ids(_read(ROOT / rel)):
            found.setdefault(row, {}).setdefault(tier, set()).add(rel.as_posix())
    return found


def scan_e2e_tcs() -> dict[str, set[str]]:
    """``{row id: {"084", ...}}`` - the TC-053 number of each E2E test function whose body names the row.

    A body runs from the end of the signature of ``def test_tc_053_nnn_...(`` to the next line at column 0 (``def``,
    ``class``, a decorator, a constant, a comment) or the end of the file. A UI-NFR-012 id counts in the scope of a
    ``UI-NFR-012`` prefix inside the body, like everywhere else.
    """
    tcs: dict[str, set[str]] = {}
    for rel, tier in _test_files():
        if tier != "e2e" or rel.suffix != ".py":
            continue
        text = _read(ROOT / rel)
        starts = list(_E2E_TC_FUNCTION.finditer(text))
        for match in starts:
            # The signature may close at column 0 (``) -> None:``); the body starts after it.
            header_end = _SIGNATURE_END.search(text, match.end())
            end = _TOP_LEVEL_LINE.search(text, header_end.end() if header_end else match.end())
            body = text[match.start() : end.start() if end else len(text)]
            rows = {
                f"GP-{kind}-{number}"
                for kind, first, rest in _TEST_ROW.findall(body)
                for number in [first, *filter(None, rest.split("/"))]
            }
            rows |= uinfr_ids(body)
            for row in rows:
                tcs.setdefault(row, set()).add(match.group(1))
    return tcs


def wave9_rows() -> dict[str, str]:
    """The rows of the wave-9 matrix in order: the REQ-053 rows, then the UI-NFR-012 rows."""
    return {**WAVE9_ROWS, **WAVE9_UINFR_ROWS}


def wave9_spec_rows() -> dict[str, str]:
    """The priority of every REQ-053 row and every UI-NFR-012 row - what a wave-9 row is checked against."""
    return {**spec_rows(), **uinfr_rows()}


def scan_wave9() -> dict[str, dict[str, set[str]]]:
    """The REQ-053 claims and the UI-NFR-012 claims of the tests in one map."""
    return {**scan_rows(), **scan_uinfr_rows()}


def load_wave9_gaps() -> dict[str, dict[str, object]]:
    return _load_gaps(WAVE9_GAPS)


def render_wave9(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, object]],
    tcs: dict[str, set[str]],
) -> str:
    header = [
        "# REQ-053 wave 9 requirement matrix GP-FR / GP-UX / GP-NFR / GP-API and UI-NFR-012 <-> test",
        "",
        "<!-- GENERATED by scripts/gp_acc_matrix.py --write from the tests - do not edit by hand. -->",
        "",
        "The rows are the REQ-053 rows of wave 9 (`WAVE9_ROWS` in `scripts/gp_acc_matrix.py`: plan section 3",
        '"Welle 9", WP 9.1-9.16, spec section 34) and the UI-NFR-012 requirements wave 9 implements',
        "(`WAVE9_UINFR_ROWS`, UI-NFR-012 v2.3 section 2.3); the priority is read from the spec tables (`API` for an",
        "API row, `MUSS`/`SOLL` for UI-NFR-012). A test claims a REQ-053 row by carrying its id (`GP-FR-144`, or the",
        "shorthand `GP-API-070/071`); it claims a UI-NFR-012 row by carrying `R-nnn` (or a range `R-021…R-027`) in",
        "a file that names UI-NFR-012. **E2E TC** lists the `TC-053-nnn` E2E functions whose body names the row.",
        "**Limit of the method:** a row counts as covered when a test file names its id; that is a claim, not proof",
        "the test exercises the row - whether it does stays a review question.",
        "Honest gaps are listed in `GP-REQ-wave9-gaps.json` with a reason and an issue: **GAP** (no test) or",
        "**partial** (the tests leave the named part unproven).",
        "",
    ]
    return _render_wave(header, "9", wave9_rows(), rows, found, gaps, tcs)


def wave9_problems(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, object]],
) -> list[str]:
    return _wave_problems("9", wave9_rows(), rows, found, gaps)


def stray_rows(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
) -> list[str]:
    """Row ids a test claims that are no row of the spec (a typo or a retired id), like the GP-ACC check."""
    return [
        f"{r}: referenced by {', '.join(sorted(f for files in found[r].values() for f in files))} but not a row of the spec"
        for r in sorted(found)
        if r not in rows
    ]


def ac_rows() -> dict[str, str]:
    """``{"§17.3 AC-n": "AC"}`` for every acceptance criterion of the workspace table (REQ-053 section 17.3)."""
    (spec,) = sorted(ROOT.glob(SPEC_GLOB))
    return {f"{AC} AC-{int(n)}": "AC" for n in _AC_ROW.findall(_read(spec))}


def domain_rows() -> dict[str, str]:
    """``{"REQ-053 W-nnn": "W"}`` for every review finding the REQ-053 spec names."""
    (spec,) = sorted(ROOT.glob(SPEC_GLOB))
    return {f"{WREQ} W-{n}": "W" for n in _W_ID.findall(_read(spec))}


def ac_ids(text: str) -> set[str]:
    """The workspace criteria a text claims: ``AC-n`` counts only in a text that names §17.3 or GP-UX-063-070."""
    if not _NAMES_WORKSPACE.search(text):
        return set()
    return {f"{AC} AC-{int(n)}" for n in _AC_ID.findall(text)}


def w_ids(text: str) -> set[str]:
    """The REQ-053 review findings a text claims: ``W-nnn`` counts only in a text that names REQ-053."""
    if not _NAMES_REQ053.search(text):
        return set()
    return {f"{WREQ} W-{n}" for n in _W_ID.findall(text)}


def scan_wave10_extra() -> dict[str, dict[str, set[str]]]:
    """``{"§17.3 AC-n" | "REQ-053 W-nnn": {tier: {file, ...}}}`` - the criteria and findings the tests claim."""
    found: dict[str, dict[str, set[str]]] = {}
    for rel, tier in _test_files():
        text = _read(ROOT / rel)
        for row in ac_ids(text) | w_ids(text):
            found.setdefault(row, {}).setdefault(tier, set()).add(rel.as_posix())
    return found


def scan_wave10_tcs() -> dict[str, set[str]]:
    """The TC-053 E2E functions per row as :func:`scan_e2e_tcs`, plus the AC / W claims of each function body.

    A body claims an ``AC-n`` (or a ``W-nnn``) when its FILE names §17.3 / GP-UX-063-070 (or REQ-053): the module
    docstring carries the spec pin, the function docstring the criterion.
    """
    tcs = {row: set(numbers) for row, numbers in scan_e2e_tcs().items()}
    for rel, tier in _test_files():
        if tier != "e2e" or rel.suffix != ".py":
            continue
        text = _read(ROOT / rel)
        names_ws, names_req = bool(_NAMES_WORKSPACE.search(text)), bool(_NAMES_REQ053.search(text))
        if not (names_ws or names_req):
            continue
        for match in _E2E_TC_FUNCTION.finditer(text):
            header_end = _SIGNATURE_END.search(text, match.end())
            end = _TOP_LEVEL_LINE.search(text, header_end.end() if header_end else match.end())
            body = text[match.start() : end.start() if end else len(text)]
            rows: set[str] = set()
            if names_ws:
                rows |= {f"{AC} AC-{int(n)}" for n in _AC_ID.findall(body)}
            if names_req:
                rows |= {f"{WREQ} W-{n}" for n in _W_ID.findall(body)}
            for row in rows:
                tcs.setdefault(row, set()).add(match.group(1))
    return tcs


def wave10_rows() -> dict[str, str]:
    """The rows of the wave-10 matrix in order: the REQ-053 rows, the workspace criteria, the domain findings."""
    return {**WAVE10_ROWS, **WAVE10_AC_ROWS, **WAVE10_DOMAIN_ROWS}


def wave10_spec_rows() -> dict[str, str]:
    """The priority of every REQ-053 row, every workspace criterion (``AC``) and every finding (``W``)."""
    return {**spec_rows(), **ac_rows(), **domain_rows()}


def scan_wave10() -> dict[str, dict[str, set[str]]]:
    """The REQ-053 row claims and the AC / W claims of the tests in one map."""
    return {**scan_rows(), **scan_wave10_extra()}


def load_wave10_gaps() -> dict[str, dict[str, object]]:
    return _load_gaps(WAVE10_GAPS)


def render_wave10(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, object]],
    tcs: dict[str, set[str]],
) -> str:
    header = [
        "# REQ-053 wave 10 requirement matrix GP-FR / GP-UX, workspace AC and Anhang A findings <-> test",
        "",
        "<!-- GENERATED by scripts/gp_acc_matrix.py --write from the tests - do not edit by hand. -->",
        "",
        "The rows are the REQ-053 rows of wave 10 (`WAVE10_ROWS` in `scripts/gp_acc_matrix.py`: plan section 3",
        '"Welle 10", WP 10.1-10.12, spec section 34), the acceptance criteria of the editor workspace',
        "(`WAVE10_AC_ROWS`, spec section 17.3; AC-11 is met by the spec itself and has no row) and the domain",
        "remainders of Anhang A 60-63 by their review finding (`WAVE10_DOMAIN_ROWS`, `W-nnn`). The priority is read",
        "from the spec (`AC` for a criterion, `W` for a finding). A test claims a GP row by carrying its id; it",
        "claims a criterion by carrying `AC-n` in a file that names §17.3 or one of GP-UX-063-070, and a finding",
        "by carrying `W-nnn` (or `W-016.6`) in a file that names REQ-053. **E2E TC** lists the `TC-053-nnn` E2E",
        "functions whose body names the row. **Limit of the method:** a row counts as covered when a test file names its id; that is a",
        "claim, not proof the test exercises the row - whether it does stays a review question.",
        "Honest gaps are listed in `GP-REQ-wave10-gaps.json` with a reason and an issue: **GAP** (no test) or",
        "**partial** (the tests leave the named part unproven).",
        "",
    ]
    return _render_wave(header, "10", wave10_rows(), rows, found, gaps, tcs)


def wave10_problems(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
    gaps: dict[str, dict[str, object]],
) -> list[str]:
    return _wave_problems("10", wave10_rows(), rows, found, gaps)


def stray_ac(
    rows: dict[str, str],
    found: dict[str, dict[str, set[str]]],
) -> list[str]:
    """Workspace criteria a test claims that the table of section 17.3 does not have (a typo or a retired id)."""
    return [
        f"{r}: referenced by {', '.join(sorted(f for files in found[r].values() for f in files))}"
        " but not a criterion of REQ-053 section 17.3"
        for r in sorted(found)
        if r.startswith(f"{AC} ") and r not in rows
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--write", action="store_true", help="regenerate the committed matrix"
    )
    parser.add_argument("--check", action="store_true", help="verify (the default)")
    args = parser.parse_args()
    ids, found, gaps = spec_ids(), scan(), load_gaps()
    rows, found_rows = spec_rows(), scan_rows()
    wave7_gaps, wave8_gaps = load_wave7_gaps(), load_wave8_gaps()
    rows9, found9, wave9_gaps = wave9_spec_rows(), scan_wave9(), load_wave9_gaps()
    rows10, found10, wave10_gaps = wave10_spec_rows(), scan_wave10(), load_wave10_gaps()
    outputs = (
        (MATRIX, render(ids, found, gaps)),
        (WAVE7_MATRIX, render_wave7(rows, found_rows, wave7_gaps)),
        (WAVE8_MATRIX, render_wave8(rows, found_rows, wave8_gaps)),
        (WAVE9_MATRIX, render_wave9(rows9, found9, wave9_gaps, scan_e2e_tcs())),
        (WAVE10_MATRIX, render_wave10(rows10, found10, wave10_gaps, scan_wave10_tcs())),
    )
    errors = (
        problems(ids, found, gaps)
        + wave7_problems(rows, found_rows, wave7_gaps)
        + wave8_problems(rows, found_rows, wave8_gaps)
        + wave9_problems(rows9, found9, wave9_gaps)
        + wave10_problems(rows10, found10, wave10_gaps)
        + stray_ac(ac_rows(), scan_wave10_extra())
        + stray_rows(rows, found_rows)
        + stray_uinfr(uinfr_rows(), scan_uinfr_rows())
        + uinfr_range_problems()
    )
    for path, text in outputs:
        if args.write:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
        elif not path.exists() or path.read_text(encoding="utf-8") != text:
            errors.append(
                f"{path.relative_to(ROOT)} is stale - run: python3 scripts/gp_acc_matrix.py --write"
            )
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
