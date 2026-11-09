"""E2E of REQ-053 wave 9 part A - service worker, offline plan read, offline buffer and sync, conflict, logout (WP 9.15, #2755).

Spec pin REQ-053 v1.13 §34 wave 9 (E-06), UI-NFR-012 v2.3 §5.1.5 (Phase 1 by CDP), §5.3.4 (Phase 3 by CDP), §5.5.
Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md, section 12, TC file v1.11); each docstring names the
source requirement of its row:
  TC-053-084  ->  service worker registered and active for /sw.js, controls the page after a reload; manifest     (UI-NFR-012
                  linked and parsed by the browser without errors, with the R-002 fields; /sw.js and the        R-001/R-002/
                  manifest served ``no-store``                                                                  R-007, R-059)
  TC-053-085  ->  app shell loads again from the worker under CDP offline: the navigation was answered by the   (R-007/R-010,
                  worker while the page reported offline                                                        §5.1.5)
  TC-053-086  ->  the last loaded plan is readable offline from IndexedDB: read-only view, "Stand von …"        (GP-UX-024 part 1,
                  banner, geometry locked; back online the editor returns                                       R-057, WP 9.2)
  TC-053-087  ->  field mode offline: "Erledigt" and a note are buffered, the chip counts them; back online the  (GP-UX-024 part 2,
                  sync sends them (snackbar), the server holds both with the capture time                      R-021/R-025/R-058)
  TC-053-088  ->  field mode offline: a bed photo is buffered and lands in the bed's gallery once online (full)  (R-058, R-060 c)
  TC-053-089  ->  a buffered "Erledigt" whose task was closed on the server meanwhile opens the conflict dialog  (R-028, WP 9.3
                  with the reason; "Verwerfen" removes it, the server keeps exactly one completion             409 task.already_closed)
  TC-053-090  ->  logout clears the read cache: the IndexedDB plan cache and the account's worker namespace     (R-055, R-056 a,
                  are gone, no kp: cache is left, the public app-shell caches stay                              SR-019)

Deviations from the issue text, each with its reason:
  * "App-Shell und zuletzt geladener Plan offline lesbar" is two cases. The plan is read offline INSIDE the running
    app (TC-053-086, a Back step in the single-page app): after an offline RELOAD the app has no signed-in user -
    the profile request fails and token persistence (R-048-R-051) is not part of wave 9 (REQ-053 §32.6 Pkt. 7) - so
    there is no ``user_key`` to read the cache under (R-055). What a reload offline must deliver is the app shell
    (TC-053-085, UI-NFR-012 §5.1.5): the login form in full mode, the app frame in light mode.
  * "Caches leer" after logout: the account's worker namespace ``kp:{user}:{tenant}``, any ``kp:`` cache and the
    IndexedDB plan cache must be gone (the ``kp:`` API cache is never filled - every API read is ``no-store``,
    see TC-053-090); the precached app shell, ``kp-static-assets`` and ``kp-runtime-config`` stay by design
    (``cachePolicy.isPublicCacheName``, R-056 a covers the read cache, not the shell) - asserted as such.
  * The conflict dialog of wave 9 offers "Behalten" / "Verwerfen" per entry (R-032 kiosk form), not the side-by-side
    comparison of R-030/R-031 (UI-NFR-012 Phase 4, not in wave 9); the case drives "Verwerfen".

Browsers: the service-worker cases (084, 085, 090) carry ``secure_context``: the stack serves http://frontend:8080,
where Chrome hides service workers and Cache Storage, so their browser starts with
``--unsafely-treat-insecure-origin-as-secure`` (``conftest.secure_context_args``). The IndexedDB cases (086-089)
need no secure context and run with the suite's normal browser. Offline is CDP ``Network.emulateNetworkConditions``
on the page (``_offline_helpers.set_network_offline``, verified on ``navigator.onLine``). Field-mode cases run on a
phone viewport (390 x 844 on desktop, the emulated 393 x 852 on ``mobile``), the others on the desktop.

Preconditions are self-provisioned through the application's own API, one fresh site per test with a UUID-derived
name (`_garden_plan_helpers.py`). Waits are anchored on state - a record in IndexedDB, an activated worker, the
banner, the chip's text, the snackbar, the stored record on the server - never on time; there is no retry loop.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from ._export_helpers import complete_task_via_api, write_solid_png
from ._garden_plan_helpers import (
    BedSpec,
    bed_photos,
    care_events,
    create_bed_task,
    provision_garden,
    rect,
    task_state,
    unique_tag,
)
from ._offline_helpers import (
    PLAN_CACHE_DB,
    PUBLIC_CACHE_PREFIXES,
    app_manifest,
    browser_now_ms,
    cache_names,
    cdp,
    indexeddb_database_names,
    navigation_entry,
    navigator_online,
    response_headers,
    set_network_offline,
    USER_CACHE_PREFIX,
    user_cache_names,
    wait_for_active_worker,
    wait_for_cached_record,
    worker_namespaces,
    worker_state,
)
from .pages.bed_site_page import BedPhotosTab
from .pages.bed_view_page import BedViewPage
from .pages.field_mode_page import set_phone_viewport
from .pages.offline_page import AccountMenu, OfflineFieldMode, OfflinePlanPage, OfflineSyncHost

#: Every case switches the network or reads browser storage over CDP (``_offline_helpers.cdp``): Chrome only.
pytestmark = pytest.mark.requires_chrome

#: "Ohne Verbindung: Du siehst den Stand von {{time}}." (``pages.gardenPlan.offline.cachedAt``), time as HH:MM.
CACHED_BANNER = re.compile(r"^Ohne Verbindung: Du siehst den Stand von .*\d{1,2}:\d{2}.*\.$")
GEOMETRY_LOCKED_OFFLINE = (
    "Ohne Verbindung kannst du den Plan nur ansehen. Zeichnen, Verschieben und Umsetzen sind gesperrt, bis die "
    "Verbindung zurück ist – nicht gespeicherte Änderungen bleiben erhalten."
)
SHEET_OFFLINE = (
    "Keine Verbindung. „Erledigt“, Notizen und Fotos werden auf dem Gerät gespeichert und übertragen, sobald du "
    "wieder online bist. Alles andere ist bis dahin gesperrt."
)
CONFLICT_TASK_CLOSED = "Die Aufgabe ist inzwischen schon erledigt oder übersprungen."
PHONE = (390, 844)
#: How long a server-side effect of the sync may take to be readable (requests, not animations).
STORED_WITHIN_S = 30

PHOTOS_NEED_STORAGE = (
    "needs the full E2E profile: only backend-full has writable attachment storage "
    "(docker-compose.e2e.yml, object-storage-full); the light backend refuses the upload"
)


# ── fixtures and local helpers ──────────────────────────────────────────────


@pytest.fixture
def phone(browser: WebDriver, device_profile: dict, record_property) -> tuple[int, int]:
    """A phone viewport: 390 x 844 on the desktop profile, the emulated 393 x 852 on ``mobile`` (read back)."""
    name = device_profile["name"]
    if name == "tablet":
        pytest.skip(
            "a phone case: the tablet profile emulates 820 x 1180; it runs on desktop and mobile"
        )
    if name == "mobile":
        inner = browser.execute_script("return [window.innerWidth, window.innerHeight];")
        actual = (int(inner[0]), int(inner[1]))
    else:
        actual = set_phone_viewport(browser, *PHONE)
    record_property("phone_viewport", f"{actual[0]}x{actual[1]} ({name})")
    return actual


def _instant_ms(stamp: str) -> int:
    """Epoch milliseconds of an ISO 8601 instant from the API (``Z``, an offset, or naive = UTC as the API stores)."""
    moment = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return int(moment.timestamp() * 1000)


def _wait_stored(driver: WebDriver, read, accept, what: str):
    """Wait until the server-side read *read()* satisfies *accept*; that value. Loud with the last value read."""
    last: list = [None]

    def _check(_d) -> bool:
        last[0] = read()
        return bool(accept(last[0]))

    try:
        WebDriverWait(driver, STORED_WITHIN_S, poll_frequency=0.5).until(_check)
    except TimeoutException as exc:
        raise AssertionError(f"{what}: the server holds {last[0]!r}") from exc
    return last[0]


def _own_account(browser: WebDriver, base_url: str) -> dict:
    """A freshly registered account, signed in in *browser*; a seed dict for the API helpers (full mode).

    TC-053-090 logs out. A logout ends the session's family AND moves the account's access-token generation
    (#2116, ``AuthService.logout``), so logging out the shared demo account would revoke the API token every
    parallel worker provisions with. The case therefore runs as its own account and logs only that one out.
    """
    import time
    import uuid

    from ._journey_helpers import _api_request
    from .conftest import _browser_login

    email = f"e2e-offline-{uuid.uuid4().hex[:10]}@example.com"
    password = "E2eOffline-12345!"
    root = base_url.rstrip("/")
    status, body = _api_request(
        f"{root}/api/v1/auth/register",
        "POST",
        None,
        {"email": email, "password": password, "display_name": "E2E Offline"},
    )
    assert status == 201, f"Self-provisioning failed: register answered {status}: {body!r}"
    status, login = _api_request(
        f"{root}/api/v1/auth/login", "POST", None, {"email": email, "password": password}
    )
    assert status == 200 and login.get("access_token"), f"login answered {status}: {login!r}"
    token = login["access_token"]
    status, tenants = _api_request(f"{root}/api/v1/tenants", "GET", token)
    assert status == 200 and isinstance(tenants, list) and tenants, f"tenants: {status} {tenants!r}"
    slug = tenants[0]["slug"]
    status, body = _api_request(f"{root}/api/v1/t/{slug}/onboarding/skip", "POST", token, {})
    assert status in (200, 204), (
        f"Self-provisioning failed: onboarding/skip answered {status}: {body!r}"
    )
    # Every cookie, whatever its path: the demo session's refresh cookie is scoped to /api/v1/auth, which
    # WebDriver's delete_all_cookies does not reach from another page - and ``execute_cdp_cmd`` does not exist on
    # the Grid's Remote driver. Left behind, the app would refresh into the demo session and the case would log
    # out the account every parallel worker provisions with.
    cdp(browser, "Network.clearBrowserCookies")
    _browser_login(browser, base_url, email, password)
    signed_in = AccountMenu(browser, base_url).signed_in_email()
    assert signed_in == email, f"the browser should be signed in as {email!r}, it is {signed_in!r}"
    return {
        "access_token": token,
        "tenant_slug": slug,
        "email": email,
        "password": password,
        "_fresh_token": (token, time.time()),
    }


def _garden_with_task(base_url: str, seed: dict, purpose: str, task_name: str):
    garden = provision_garden(
        base_url, seed, purpose=purpose, beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),)
    )
    bed = garden.bed_key("Beet 1")
    task = create_bed_task(base_url, seed, bed_key=bed, name=task_name, category="watering")
    return garden, bed, task


def _cache_sheet_then_go_offline(
    field: OfflineFieldMode, site_key: str, bed: str, what: str
) -> str:
    """Open the bed sheet online (its copy lands in IndexedDB), close it, go offline, open it from the cache.

    Returns the sheet's "Stand von" banner. The offline half starts only once the cached record exists and the
    sheet reports the offline capture code as loaded (``data-offline-capture-ready``).
    """
    field.open(site_key)
    field.tap_bed(bed)
    wait_for_cached_record(
        field.driver, PLAN_CACHE_DB, "bedSheets", bed, f"{what}: the sheet cached online"
    )
    field.wait_for_offline_capture_ready(what)
    field.close_sheet()
    set_network_offline(field.driver, True)
    return field.tap_bed_offline(bed, what)


# ── TC-053-084 ──────────────────────────────────────────────────────────────


@pytest.mark.secure_context
@pytest.mark.requires_desktop
def test_tc_053_084_service_worker_active_and_manifest_served(
    browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-084 — one service worker at /sw.js, active and in control; the manifest served and parsed (UI-NFR-012 §5.1.5).

    Source: UI-NFR-012 R-001, R-002, R-007, R-059; REQ-053 WP 9.1. Precondition (API): a site with one bed. The plan
    is opened; the registration for ``/`` gets an ``activated`` worker whose script is ``/sw.js``; after a reload the
    page is controlled by it. The document links ``/manifest.json``; CDP ``Page.getAppManifest`` returns it without
    errors, with ``name``, ``short_name``, ``start_url``, ``display: standalone``, both colours and a 192 and a 512
    icon. ``/sw.js`` and ``/manifest.json`` answer 200 with ``Cache-Control`` containing ``no-store``. Breaks if no
    worker registers, a second script registers, the worker never takes control, the manifest is missing or
    broken, or nginx lets a browser cache the worker script.
    """
    plan = OfflinePlanPage(browser, base_url)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc084",
        beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    plan.open(garden.site_key)
    state = wait_for_active_worker(browser, "TC-053-084: after the first visit")
    assert state["activeUrl"].endswith("/sw.js"), (
        f"TC-053-084: the worker script is /sw.js, it is {state}"
    )
    assert state["scope"].rstrip("/") == base_url.rstrip("/"), (
        f"TC-053-084: one worker for the whole origin (scope '/'), it has {state['scope']!r}"
    )

    plan.reload_plan(garden.site_key)
    controlled = worker_state(browser)
    assert (controlled["controllerUrl"] or "").endswith("/sw.js"), (
        f"TC-053-084: after a reload /sw.js controls the page: {controlled}"
    )
    screenshot("053_084_01_controlled", "Plan geladen, Service Worker aktiv und steuert die Seite")

    assert plan.manifest_link().endswith("/manifest.json"), (
        f"TC-053-084: the document links /manifest.json, it links {plan.manifest_link()!r}"
    )
    manifest = app_manifest(browser)
    assert manifest.get("url", "").endswith("/manifest.json"), (
        f"TC-053-084: manifest url {manifest.get('url')!r}"
    )
    assert manifest.get("errors") == [], (
        f"TC-053-084: the browser reports manifest errors: {manifest.get('errors')}"
    )
    parsed = json.loads(manifest.get("data") or "{}")
    assert parsed.get("name") and parsed.get("short_name"), (
        f"TC-053-084: name/short_name missing: {parsed}"
    )
    assert parsed.get("start_url") and parsed.get("display") == "standalone", (
        f"TC-053-084: start_url and display=standalone (R-002): {parsed}"
    )
    assert parsed.get("theme_color") and parsed.get("background_color"), (
        f"TC-053-084: colours missing: {parsed}"
    )
    sizes = {icon.get("sizes") for icon in parsed.get("icons") or []}
    assert {"192x192", "512x512"} <= sizes, (
        f"TC-053-084: icons of 192 and 512 px (R-002), it has {sizes}"
    )

    for path in ("/sw.js", "/manifest.json"):
        headers = response_headers(browser, path)
        assert headers["status"] == 200, f"TC-053-084: GET {path} answered {headers}"
        assert "no-store" in (headers.get("cacheControl") or ""), (
            f"TC-053-084: {path} must be served no-store (R-059), Cache-Control is {headers.get('cacheControl')!r}"
        )


# ── TC-053-085 ──────────────────────────────────────────────────────────────


@pytest.mark.secure_context
@pytest.mark.requires_desktop
def test_tc_053_085_app_shell_reloads_offline_from_the_worker(
    browser: WebDriver, base_url: str, e2e_seed_data: dict, app_mode: str, screenshot
) -> None:
    """TC-053-085 — under CDP offline a reload is answered by the worker and the app shell renders (UI-NFR-012 §5.1.5).

    Source: UI-NFR-012 R-007, R-008, R-010; REQ-053 WP 9.1. Precondition: the plan was opened online and the worker
    controls the page (one online reload, so the lazy route chunks pass the worker's asset cache). Then the page goes
    offline (``navigator.onLine`` false, verified) and reloads. Asserted: the navigation entry has ``workerStart > 0``
    (the worker answered), the page still reports offline, the worker still controls it, and the app rendered its
    shell - the login form in full mode (no session can be restored offline, R-050 not in wave 9), the app frame with
    the connectivity indicator in light mode. Breaks if the reload shows the browser's offline error page, if the
    document did not come from the worker, or if the run was not offline at all.
    """
    plan = OfflinePlanPage(browser, base_url)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc085",
        beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    plan.open(garden.site_key)
    wait_for_active_worker(browser, "TC-053-085: after the first visit")
    plan.reload_plan(garden.site_key)
    assert (worker_state(browser)["controllerUrl"] or "").endswith("/sw.js"), (
        "TC-053-085: precondition - the worker controls the page before going offline"
    )

    set_network_offline(browser, True)
    shell = plan.reload_offline("TC-053-085: the reload under CDP offline")
    entry = navigation_entry(browser)
    assert entry["workerStart"] > 0, f"TC-053-085: the document must come from the worker: {entry}"
    assert navigator_online(browser) is False, "TC-053-085: the reload ran offline"
    assert (worker_state(browser)["controllerUrl"] or "").endswith("/sw.js"), (
        "TC-053-085: the worker controls the page loaded offline"
    )
    expected = "login" if app_mode == "full" else "frame"
    assert shell == expected, (
        f"TC-053-085: offline the app shows its {expected} ({app_mode} mode), it shows {shell!r}"
    )
    screenshot(
        "053_085_01_shell_offline", "Neu geladen ohne Verbindung: App-Shell aus dem Service Worker"
    )


# ── TC-053-086 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_086_last_loaded_plan_is_readable_offline_with_its_time(
    browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-086 — the plan read online is shown offline from IndexedDB, read-only, with "Stand von" (GP-UX-024).

    Source: REQ-053 GP-UX-024 part 1, UI-NFR-012 R-057, WP 9.2. Precondition (API): a site with two beds. The plan
    is opened online (its record appears in ``kp-plan-cache/plans`` under ``{user}:{tenant}:{site}``), then the user
    goes to the site page with "Zurück zum Standort", the page goes offline, and Back returns to the plan inside the
    app. Asserted: the read-only view (not the offline miss) draws both beds, the banner reads "Ohne Verbindung: Du
    siehst den Stand von <Uhrzeit>.", the lock text is the offline one, "Export & Import" is not offered; back online
    the editor replaces the read-only view and the banner is gone. Breaks if the plan is not cached, the cached plan
    is not offered offline, the banner is missing or a cached plan can be edited.
    """
    plan = OfflinePlanPage(browser, base_url)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc086",
        beds=(
            BedSpec("Beet A", rect(1.0, 1.0, 2.0, 1.0)),
            BedSpec("Beet B", rect(5.0, 5.0, 2.0, 1.0)),
        ),
    )
    beds = {garden.bed_key("Beet A"), garden.bed_key("Beet B")}
    plan.open(garden.site_key)
    wait_for_cached_record(
        browser, PLAN_CACHE_DB, "plans", garden.site_key, "TC-053-086: the plan read online"
    )
    plan.leave_to_site(garden.site_key)

    set_network_offline(browser, True)
    plan.go_back_to_plan(garden.site_key)
    banner = plan.wait_for_read_only("TC-053-086")
    assert CACHED_BANNER.match(banner), (
        f"TC-053-086: the banner names the time of the copy: {banner!r}"
    )
    assert plan.text_of(plan.GEOMETRY_LOCKED) == GEOMETRY_LOCKED_OFFLINE, (
        f"TC-053-086: the lock says why: {plan.text_of(plan.GEOMETRY_LOCKED)!r}"
    )
    drawn = set(plan.drawn_object_keys())
    assert beds <= drawn, (
        f"TC-053-086: both beds are drawn from the cache: {sorted(beds)} of {sorted(drawn)}"
    )
    assert not plan.is_present(plan.IO_MENU), (
        "TC-053-086: 'Export & Import' needs the server and is hidden offline"
    )
    screenshot("053_086_01_plan_offline", "Plan ohne Verbindung: schreibgeschützt, „Stand von …“")

    set_network_offline(browser, False)
    plan.wait_for_live_editor("TC-053-086: back online")
    assert not plan.has_cached_banner(), "TC-053-086: back online the banner is gone"
    screenshot(
        "053_086_02_back_online",
        "Wieder online: der Editor ersetzt die Ansicht aus dem Zwischenspeicher",
    )


# ── TC-053-087 ──────────────────────────────────────────────────────────────


def test_tc_053_087_done_and_note_are_buffered_offline_and_synced_online(
    phone: tuple[int, int], browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-087 — offline "Erledigt" and a note wait on the device, are sent back online, the server has both (GP-UX-024).

    Source: REQ-053 GP-UX-024 part 2, UI-NFR-012 R-021, R-025, R-058, §5.3.4; WP 9.4. Precondition (API): "Beet 1"
    with an open watering task due today. Field mode online opens the sheet once (cached), then the page goes
    offline and the sheet is opened from the cache: the "Stand von" banner and the offline notice show. "Erledigt"
    -> "Fertig" closes the dialog, the task shows "Wartet auf Übertragung"; the note chip stores a unique text; the
    app bar reads "2 nicht übertragen". Nothing has reached the server yet. Back online the snackbar says
    "2 Einträge übertragen.", the chip disappears, the task is ``completed`` with exactly one care event, the note is
    stored once with its ``client_event_id``; both carry a ``performed_at`` inside the offline window (the capture
    time, not the send time). Breaks if offline writes are refused or lost, sent twice, sent with the sync time, or
    if the sync never starts by itself.
    """
    field = OfflineFieldMode(browser, base_url)
    host = OfflineSyncHost(browser, base_url)
    task_name = f"Gießen {unique_tag()}"
    note = f"Schnecken am Rand {unique_tag()}"
    garden, bed, task = _garden_with_task(base_url, e2e_seed_data, "tc087", task_name)

    banner = _cache_sheet_then_go_offline(field, garden.site_key, bed, "TC-053-087")
    went_offline = browser_now_ms(browser)
    assert CACHED_BANNER.match(banner), (
        f"TC-053-087: the sheet names the time of its copy: {banner!r}"
    )
    assert field.sheet_offline_text() == SHEET_OFFLINE, (
        f"TC-053-087: the sheet says what works offline: {field.sheet_offline_text()!r}"
    )
    screenshot("053_087_01_sheet_offline", "Beet-Sheet ohne Verbindung aus dem Zwischenspeicher")

    field.tap_done(task)
    field.tap_finish("TC-053-087: 'Fertig' offline")
    assert field.wait_for_done_queued(task, "TC-053-087") == "Wartet auf Übertragung"
    assert not field.is_done_offered(task), (
        "TC-053-087: a buffered task offers no second 'Erledigt'"
    )
    field.open_note()
    field.submit_note(note, "TC-053-087: the note offline")
    host.wait_for_queue_chip("2 nicht übertragen", "TC-053-087: two entries wait")
    host.assert_app_bar_fits("TC-053-087: offline with two entries waiting (#2815)")
    screenshot(
        "053_087_02_buffered", "Erledigt und Notiz auf dem Gerät gespeichert: „2 nicht übertragen“"
    )

    assert task_state(base_url, e2e_seed_data, task)["status"] != "completed", (
        "TC-053-087: nothing reached the server while offline"
    )
    assert care_events(base_url, e2e_seed_data, bed, category="note") == [], (
        "TC-053-087: the note did not reach the server while offline"
    )

    went_online = browser_now_ms(browser)
    set_network_offline(browser, False)
    message = field.wait_for_snackbar_message("übertragen.", "TC-053-087: after the sync")
    assert message == "2 Einträge übertragen.", (
        f"TC-053-087: the sync names what it sent: {message!r}"
    )
    host.wait_for_queue_chip_gone("TC-053-087: after the sync")
    screenshot("053_087_03_synced", "Wieder online: 2 Einträge übertragen")

    status = _wait_stored(
        browser,
        lambda: task_state(base_url, e2e_seed_data, task)["status"],
        lambda value: value == "completed",
        "TC-053-087: the buffered completion",
    )
    assert status == "completed"
    completions = [
        e for e in care_events(base_url, e2e_seed_data, bed) if e.get("task_key") == task
    ]
    notes = care_events(base_url, e2e_seed_data, bed, category="note")
    assert len(completions) == 1, (
        f"TC-053-087: one completion is one care event, found {completions}"
    )
    assert [n["summary"] for n in notes] == [note], f"TC-053-087: the note is stored once: {notes}"
    # The note's care event carries its ``client_event_id``; a completion keeps it on the task
    # (``completion_client_event_id``, not in the API answer) - its capture time is what shows the buffer.
    assert notes[0].get("client_event_id"), (
        f"TC-053-087: the note came through the buffer: {notes[0]}"
    )
    for label, event in (("completion", completions[0]), ("note", notes[0])):
        captured = _instant_ms(event["performed_at"])
        assert went_offline - 1000 <= captured <= went_online, (
            f"TC-053-087: the {label} carries its capture time (offline {went_offline} ... online {went_online}), "
            f"performed_at is {event['performed_at']} ({captured})"
        )


# ── TC-053-088 ──────────────────────────────────────────────────────────────


def test_tc_053_088_bed_photo_is_buffered_offline_and_reaches_the_gallery(
    phone: tuple[int, int],
    browser: WebDriver,
    app_mode: str,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
    tmp_path: Path,
) -> None:
    """TC-053-088 — "Foto vom Beet" offline waits on the device and lands in the bed's gallery back online (R-058).

    Source: UI-NFR-012 R-058, R-060 (c), REQ-053 GP-FR-051; WP 9.4. Full profile only (attachment storage).
    Precondition (API): "Beet 1" without a photo. The sheet is cached online, then opened offline; a generated PNG
    goes through the upload dialog, the snackbar says it was stored on the device, the chip reads
    "1 nicht übertragen" and the server's gallery is still empty. Back online the sync says "1 Eintrag übertragen.",
    the gallery holds exactly one photo and it is the cover. Breaks if a photo cannot be captured offline, is lost or
    sent twice, or lands somewhere else.
    """
    if app_mode != "full":
        pytest.skip(f"TC-053-088 (photo upload) {PHOTOS_NEED_STORAGE}")
    field = OfflineFieldMode(browser, base_url)
    photos = BedPhotosTab(browser, base_url)
    host = OfflineSyncHost(browser, base_url)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc088",
        beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    bed = garden.bed_key("Beet 1")
    picture = write_solid_png(tmp_path / "beet-offline.png")

    _cache_sheet_then_go_offline(field, garden.site_key, bed, "TC-053-088")
    field.tap_bed_photo()
    photos.choose_file(str(picture))
    photos.wait_for_preview("TC-053-088: the chosen picture")
    photos.confirm_upload("TC-053-088: 'Hochladen' offline")
    message = field.wait_for_snackbar_message(
        "auf dem Gerät gespeichert", "TC-053-088: after the offline upload"
    )
    assert message.startswith("Foto auf dem Gerät gespeichert"), f"TC-053-088: {message!r}"
    host.wait_for_queue_chip("1 nicht übertragen", "TC-053-088: the photo waits")
    host.assert_app_bar_fits("TC-053-088: offline with the photo waiting (#2815)")
    assert bed_photos(base_url, e2e_seed_data, bed)["photos"] == [], (
        "TC-053-088: nothing uploaded while offline"
    )
    screenshot(
        "053_088_01_photo_buffered", "Foto vom Beet ohne Verbindung auf dem Gerät gespeichert"
    )

    set_network_offline(browser, False)
    synced = field.wait_for_snackbar_message("übertragen.", "TC-053-088: after the sync")
    assert synced == "1 Eintrag übertragen.", f"TC-053-088: the sync names what it sent: {synced!r}"
    host.wait_for_queue_chip_gone("TC-053-088: after the sync")
    gallery = _wait_stored(
        browser,
        lambda: bed_photos(base_url, e2e_seed_data, bed),
        lambda value: len(value["photos"]) > 0,
        "TC-053-088: the synced photo",
    )
    assert len(gallery["photos"]) == 1, f"TC-053-088: exactly one photo at the bed: {gallery}"
    assert gallery["cover_photo_ref"] == gallery["photos"][0]["attachment_id"], (
        f"TC-053-088: the first photo is the cover: {gallery}"
    )
    screenshot("053_088_02_photo_synced", "Wieder online: Foto übertragen")

    BedViewPage(browser, base_url).open(bed, "photos")
    synced_id = gallery["photos"][0]["attachment_id"]
    assert photos.wait_for_photo_count(1, "TC-053-088: the bed's gallery") == [synced_id]
    photos.wait_for_cover(synced_id, "TC-053-088: the gallery")
    screenshot("053_088_03_gallery", "Galerie des Beets: genau ein Foto, als Titelbild markiert")


# ── TC-053-089 ──────────────────────────────────────────────────────────────


def test_tc_053_089_task_closed_meanwhile_opens_the_conflict_dialog(
    phone: tuple[int, int], browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-089 — a buffered "Erledigt" for a task closed on the server meanwhile is a conflict, never a 2nd close (R-028).

    Source: UI-NFR-012 R-028, R-032; REQ-053 WP 9.3 (``409 task.already_closed``), WP 9.4. Precondition (API):
    "Beet 1" with an open watering task. Offline, "Erledigt" -> "Fertig" buffers the completion; meanwhile the task
    is completed on the server (``POST /tasks/{key}/complete`` - a second device). Back online the conflict dialog
    opens by itself with the entry (status ``conflict``) and the reason "Die Aufgabe ist inzwischen schon erledigt
    oder übersprungen."; "Verwerfen" removes it and the chip disappears. The server holds exactly one completion of
    the task - the other device's, timed at its close, not at the earlier offline capture. Breaks if the buffered write closes the task a
    second time, if the conflict is silent, or if "Verwerfen" leaves the entry.
    """
    field = OfflineFieldMode(browser, base_url)
    host = OfflineSyncHost(browser, base_url)
    task_name = f"Gießen {unique_tag()}"
    garden, bed, task = _garden_with_task(base_url, e2e_seed_data, "tc089", task_name)

    _cache_sheet_then_go_offline(field, garden.site_key, bed, "TC-053-089")
    field.tap_done(task)
    field.tap_finish("TC-053-089: 'Fertig' offline")
    host.wait_for_queue_chip("1 nicht übertragen", "TC-053-089: the completion waits")
    # The buffered completion is captured by now (the chip counts it): every instant it can carry lies before
    # this mark. The other device closes the task strictly after it.
    captured_by = browser_now_ms(browser)
    other_device_at = browser_now_ms(browser)
    while other_device_at <= captured_by:
        other_device_at = browser_now_ms(browser)
    complete_task_via_api(base_url, e2e_seed_data, task)

    set_network_offline(browser, False)
    entries = host.wait_for_conflict_entries("TC-053-089: back online")
    assert len(entries) == 1, f"TC-053-089: one conflicting entry: {entries}"
    (entry,) = entries
    assert entry["status"] == "conflict", f"TC-053-089: the entry is a conflict: {entry}"
    assert entry["reason"] == CONFLICT_TASK_CLOSED, f"TC-053-089: the reason: {entry['reason']!r}"
    assert task_name in entry["text"], f"TC-053-089: the entry names the task: {entry['text']!r}"
    screenshot("053_089_01_conflict", "Konflikt: Aufgabe inzwischen erledigt")

    host.discard(entry["id"], "TC-053-089: 'Verwerfen'")
    host.wait_for_queue_chip_gone("TC-053-089: after 'Verwerfen'")
    completions = [
        e for e in care_events(base_url, e2e_seed_data, bed) if e.get("task_key") == task
    ]
    assert len(completions) == 1, (
        f"TC-053-089: exactly the other device's completion: {completions}"
    )
    # The buffered "Erledigt" was captured before the other device closed the task; the stored completion is
    # the other device's - timed at or after its close, never at the earlier capture time.
    assert _instant_ms(completions[0]["performed_at"]) >= other_device_at, (
        f"TC-053-089: the stored completion is the other device's, not the buffered one: {completions[0]}"
    )
    assert task_state(base_url, e2e_seed_data, task)["status"] == "completed"
    screenshot("053_089_02_discarded", "Eintrag verworfen")


# ── TC-053-090 ──────────────────────────────────────────────────────────────


@pytest.mark.secure_context
@pytest.mark.requires_auth
@pytest.mark.requires_desktop
def test_tc_053_090_logout_clears_the_read_cache_and_the_account_cache(
    browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-090 — "Abmelden" removes the IndexedDB plan cache and the account's worker namespace (R-056 a, SR-019).

    Source: UI-NFR-012 R-055, R-056 (a); REQ-053 SR-019, WP 9.1/9.2. Full mode (light mode has no logout).
    Runs as a freshly registered account (``_own_account``): a logout revokes the account's access tokens.
    Precondition: the worker controls the page, the plan was read (a record in ``kp-plan-cache/plans``) and the tab
    announced its namespace ``kp:{user}:{tenant}`` to the worker (its persisted state ``kp-sw-state`` names it).
    "Abmelden" (nothing buffered, so no confirmation) ends on the login form. Asserted: ``kp-plan-cache`` is no
    longer an IndexedDB database, the worker holds no ``kp:`` namespace any more, no ``kp:`` Cache Storage cache is
    left, and the public app-shell caches (``workbox-precache…``) are still there - the cache list was read, it is
    not merely empty. Breaks if the next person on the device could read the previous account's plans offline.

    Not asserted: a filled ``kp:{user}:{tenant}`` API cache before the logout. The backend answers every
    ``/api/v1/`` read ``Cache-Control: no-store`` (MT-044, ``main.py``) and the worker respects it (G-W9 c,
    ``cachePolicy.isCacheableApiResponse``), so the allowlisted reads are never written to Cache Storage; the
    offline plan comes from IndexedDB (TC-053-086). Named as a finding in the WP 9.15 report.
    """
    plan = OfflinePlanPage(browser, base_url)
    account = _own_account(browser, base_url)
    garden = provision_garden(
        base_url,
        account,
        purpose="tc090",
        beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    plan.open(garden.site_key)
    wait_for_active_worker(browser, "TC-053-090: after the first visit")
    plan.reload_plan(garden.site_key)
    wait_for_cached_record(
        browser, PLAN_CACHE_DB, "plans", garden.site_key, "TC-053-090: the plan read"
    )
    try:
        WebDriverWait(browser, 15, poll_frequency=0.5).until(
            lambda d: any(n.startswith(USER_CACHE_PREFIX) for n in worker_namespaces(d) or [])
        )
    except TimeoutException as exc:
        raise AssertionError(
            f"TC-053-090: precondition - the tab announced kp:{{user}}:{{tenant}} to the worker; it holds "
            f"{worker_namespaces(browser)}"
        ) from exc
    screenshot(
        "053_090_01_cached", "Vor dem Abmelden: Plan im Zwischenspeicher, Namensraum beim Worker"
    )

    AccountMenu(browser, base_url).logout("TC-053-090")

    def _cleared(d) -> bool:
        namespaces = worker_namespaces(d) or []
        return (
            PLAN_CACHE_DB not in indexeddb_database_names(d)
            and not user_cache_names(d)
            and not any(n.startswith(USER_CACHE_PREFIX) for n in namespaces)
        )

    try:
        WebDriverWait(browser, 15, poll_frequency=0.5).until(_cleared)
    except TimeoutException as exc:
        raise AssertionError(
            f"TC-053-090: after the logout the read cache must be gone; databases "
            f"{indexeddb_database_names(browser)}, caches {cache_names(browser)}, worker namespaces "
            f"{worker_namespaces(browser)}"
        ) from exc
    left = cache_names(browser)
    assert any(name.startswith(PUBLIC_CACHE_PREFIXES) for name in left), (
        f"TC-053-090: the app shell's caches stay (they hold no account data): {left}"
    )
    screenshot("053_090_02_logged_out", "Nach dem Abmelden: Lesecache und Konto-Namensraum geleert")
