"""E2E tests for REQ-024 -- cross-tenant negative probes (audit MT-024, #2120).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-024.md):
  TC-024-094  Deep-Link auf eine Pflanze eines fremden Tenants zeigt "nicht gefunden"
  TC-024-095  Bearbeiten ueber einen Deep-Link mit fremdem Schluessel aendert nichts
  TC-024-096  Globaler Seed-Duenger ist fuer einen Gaertner nicht aenderbar
  TC-024-097  Naehrstoffplan eines fremden Tenants ist nicht druckbar

What these probes add over the integration layer
------------------------------------------------
``src/backend/tests/integration/`` already drives the real router, service and
repository with another tenant's keys (NFR-008 §5.4). What only a deployed stack
can show is the *whole* path: the nginx/Vite proxy, the JWT a real login issued,
the active tenant the SPA derives from it, and what the detail route then puts on
screen. A handler that answered 403 instead of 404, or a page that rendered a
foreign record's name in a toast or a title before the error branch won, passes
every API-level probe and fails here.

Isolation (``e2e-test-stability`` §A)
-------------------------------------
Every test registers its **own** two gardeners ("Anna" and "Bernd"), each with a
fresh personal tenant, and creates Bernd's records itself. Nothing is shared
with the demo account, with another test of this module, or with another xdist
worker. The one shared object is the global seed fertilizer of TC-024-096, and
that probe never sends a value that would change it: the write attempt re-sends
the stored name, so a broken gate shows up as a ``200`` instead of a ``403``
without corrupting the catalogue every other test reads.

Mode
----
Two tenants need two accounts, which only full mode has; the module carries the
harness's ``requires_auth`` marker, so ``conftest.pytest_collection_modifyitems``
skips it in light mode with the reason "requires full auth mode". The nightly
profiles that run it are ``full`` and ``full-mobile``.

Routes
------
The test cases write the deep link as ``/t/garten-anna/pflanzen/...``. The SPA's
routes carry no tenant segment: the active tenant comes from the session
(``kp_active_tenant_slug``), and the API call underneath is
``/api/v1/t/<Annas slug>/...``. Opening ``/pflanzen/plant-instances/<key>`` while
signed in as Anna is therefore exactly the "foreign key in my own tenant" request
the cases describe; each test anchors on Anna's slug being the active one first.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver

from ._auth_helpers import clear_auth_session
from .conftest import _E2E_TOGGLEABLE_MODULES, _browser_login
from .pages import (
    FertilizerDetailPage,
    LocationDetailPage,
    NutrientPlanDetailPage,
    PlantInstanceDetailPage,
    PrintButtonPage,
    TankDetailPage,
)
from .pages.base_page import BasePage

pytestmark = pytest.mark.requires_auth

#: Every outbound call of this module is bounded; the stack is local to the run.
_HTTP_TIMEOUT = 15
#: Where the SPA keeps the active tenant (`store/slices/tenantSlice.ts`).
_ACTIVE_TENANT_STORAGE_KEY = "kp_active_tenant_slug"
#: The seed fertilizer TC-024-096 names (`seed_data/fertilizers.yaml`).
_SEED_FERTILIZER_NAME = "CalMag"
_SEED_FERTILIZER_BRAND = "Terra Aquatica"


# -- HTTP helpers --------------------------------------------------------------


def _request(
    method: str, url: str, *, token: str | None = None, body: dict | None = None
) -> tuple[int, bytes, str]:
    """Send one request; return ``(status, raw body, content type)`` for any status."""
    headers = {"Accept": "application/json, application/pdf"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
        return exc.code, exc.read(), content_type


def _call(
    method: str, url: str, *, token: str | None = None, body: dict | None = None
) -> tuple[int, Any]:
    """Like :func:`_request`, with the body decoded as JSON where it is JSON."""
    status, raw, _content_type = _request(method, url, token=token, body=body)
    if not raw:
        return status, None
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, raw.decode(errors="replace")


def _expect(status: int, payload: Any, expected: int, what: str) -> Any:
    """Return *payload* when *status* is *expected*; fail loudly, quoting it, otherwise."""
    if status != expected:
        raise AssertionError(f"{what}: expected HTTP {expected}, got {status}: {payload!r}")
    return payload


def _expect_2xx(status: int, payload: Any, what: str) -> Any:
    if not 200 <= status < 300:
        raise AssertionError(f"{what}: expected a 2xx response, got {status}: {payload!r}")
    return payload


# -- Self-provisioned gardeners ------------------------------------------------


@dataclass(frozen=True)
class Gardener:
    """A freshly registered account and the personal tenant it was given."""

    label: str
    email: str
    password: str
    token: str
    slug: str
    api: str

    @property
    def tenant_api(self) -> str:
        """Base of every tenant-scoped route of this gardener's own tenant."""
        return f"{self.api}/t/{self.slug}"


def _provision_gardener(base_url: str, label: str) -> Gardener:
    """Register, log in and prepare one gardener; fail loudly on any step.

    The account is new on every call (UUID-derived address), so its personal
    tenant holds nothing but what the test creates in it. Onboarding is skipped
    and every toggleable module enabled server-side: a fresh account is a
    beginner, and REQ-042's ModuleGuard would otherwise render the "module
    hidden" placeholder on the nutrition and tank routes instead of the route
    the probe is about (the same map ``conftest.e2e_seed_data`` writes for the
    demo user).
    """
    api = f"{base_url.rstrip('/')}/api/v1"
    suffix = uuid.uuid4().hex[:12]
    email = f"e2e-xt-{label.lower()}-{suffix}@example.com"
    password = f"Xt-{suffix}-Garten!"

    status, payload = _call(
        "POST",
        f"{api}/auth/register",
        body={"email": email, "password": password, "display_name": f"Garten {label} {suffix}"},
    )
    _expect_2xx(status, payload, f"register {label}")

    status, login = _call("POST", f"{api}/auth/login", body={"email": email, "password": password})
    token = _expect(status, login, 200, f"log in as {label}").get("access_token")
    if not token:
        raise AssertionError(f"log in as {label}: no access_token in {login!r}")

    status, tenants = _call("GET", f"{api}/tenants", token=token)
    _expect(status, tenants, 200, f"list the tenants of {label}")
    if not isinstance(tenants, list) or len(tenants) != 1:
        raise AssertionError(
            f"{label} should own exactly the personal tenant created at registration, got {tenants!r}"
        )
    slug = tenants[0]["slug"]

    gardener = Gardener(label, email, password, token, slug, api)
    status, payload = _call("POST", f"{gardener.tenant_api}/onboarding/skip", token=token, body={})
    _expect_2xx(status, payload, f"skip onboarding for {label}")
    status, payload = _call(
        "PATCH",
        f"{gardener.tenant_api}/user-preferences",
        token=token,
        body={"module_visibility": {k: "enabled" for k in _E2E_TOGGLEABLE_MODULES}},
    )
    _expect_2xx(status, payload, f"enable all modules for {label}")
    return gardener


@pytest.fixture
def gardens(base_url: str) -> tuple[Gardener, Gardener]:
    """Anna and Bernd: two fresh tenants, and Anna is no member of Bernd's."""
    anna = _provision_gardener(base_url, "Anna")
    bernd = _provision_gardener(base_url, "Bernd")
    status, anna_tenants = _call("GET", f"{anna.api}/tenants", token=anna.token)
    _expect(status, anna_tenants, 200, "list Anna's tenants")
    anna_slugs = {t["slug"] for t in anna_tenants}
    assert bernd.slug not in anna_slugs, (
        f"Precondition: Anna must not be a member of Bernd's tenant {bernd.slug!r}, "
        f"but her tenants are {sorted(anna_slugs)}"
    )
    return anna, bernd


# -- Bernd's records (created through the API, in his own tenant) -------------


def _create(gardener: Gardener, collection: str, body: dict) -> dict:
    status, payload = _call(
        "POST", f"{gardener.tenant_api}/{collection}", token=gardener.token, body=body
    )
    return _expect(status, payload, 201, f"{gardener.label} creates a {collection} row")


def _read(gardener: Gardener, path: str) -> dict:
    status, payload = _call("GET", f"{gardener.tenant_api}/{path}", token=gardener.token)
    return _expect(status, payload, 200, f"{gardener.label} reads {path}")


def _any_species_key(gardener: Gardener) -> str:
    """Key of a global catalogue species, which every tenant can plant."""
    status, payload = _call("GET", f"{gardener.api}/species?limit=1", token=gardener.token)
    items = _expect(status, payload, 200, "list the species catalogue").get("items") or []
    if not items:
        raise AssertionError(
            "The species catalogue is empty, so no plant can be created. The E2E stack "
            "loads the global seed at start-up; an empty catalogue means that seed failed."
        )
    return items[0]["key"]


def _create_plant(gardener: Gardener, name: str) -> dict:
    return _create(
        gardener,
        "plant-instances",
        {
            "instance_id": f"E2E-XT-{uuid.uuid4().hex[:10]}",
            "species_key": _any_species_key(gardener),
            "plant_name": name,
            "planted_on": date.today().isoformat(),
        },
    )


def _create_site(gardener: Gardener, name: str) -> dict:
    return _create(
        gardener,
        "sites",
        {"name": name, "climate_zone": "8a", "total_area_m2": 20, "timezone": "Europe/Berlin"},
    )


def _create_location(gardener: Gardener, site_key: str, name: str) -> dict:
    return _create(
        gardener,
        "locations",
        {"name": name, "site_key": site_key, "location_type_key": "greenhouse", "area_m2": 12},
    )


def _create_tank(gardener: Gardener, location_key: str, name: str) -> dict:
    return _create(
        gardener,
        "tanks",
        {
            "name": name,
            "tank_type": "nutrient",
            "volume_liters": 60.0,
            "location_key": location_key,
        },
    )


def _create_nutrient_plan(gardener: Gardener, name: str) -> dict:
    return _create(
        gardener,
        "nutrient-plans",
        {"name": name, "description": "E2E cross-tenant probe (#2120)"},
    )


def _subset(row: dict, fields: tuple[str, ...]) -> dict:
    return {f: row.get(f) for f in fields}


# -- Browser helpers -----------------------------------------------------------


def _sign_in(page: BasePage, gardener: Gardener) -> None:
    """Put the browser into *gardener*'s session, with their tenant active.

    The refresh cookie is scoped to ``/api/v1/auth``; parking the browser on that
    path first lets the plain cookie wipe reach it even where CDP is missing (the
    reasoning of ``conftest._switch_account``). The persisted tenant slug of the
    previous account is removed too, so the SPA cannot start in a tenant the new
    account does not belong to.

    Ends on a positive anchor -- the SPA persisted *this* gardener's slug as the
    active tenant -- because every probe below means "a foreign key, requested in
    my own tenant", and that only holds once the SPA has resolved which tenant
    that is.
    """
    driver = page.driver
    driver.get(f"{page.base_url}/api/v1/auth/csrf")
    driver.delete_all_cookies()
    clear_auth_session(driver)
    driver.execute_script(
        "window.localStorage.removeItem(arguments[0]);", _ACTIVE_TENANT_STORAGE_KEY
    )
    _browser_login(driver, page.base_url, gardener.email, gardener.password)

    def _active_slug(d: WebDriver) -> str | None:
        return d.execute_script(
            "return window.localStorage.getItem(arguments[0]);", _ACTIVE_TENANT_STORAGE_KEY
        )

    try:
        page.poll(15).until(lambda d: _active_slug(d) == gardener.slug)
    except TimeoutException as exc:
        raise AssertionError(
            f"Signed in as {gardener.label}, but the SPA's active tenant is "
            f"{_active_slug(driver)!r} instead of {gardener.slug!r}; a probe run now would "
            f"not be asking in {gardener.label}'s own tenant."
        ) from exc


def _missing_key() -> str:
    """A key that exists in no tenant (the 'frei erfundener Schluessel' of TC-024-094)."""
    return f"e2e-xt-missing-{uuid.uuid4().hex[:12]}"


def _require_not_found(page: BasePage, path: str, page_root: tuple[str, str], what: str) -> str:
    """Open *path* directly, require the not-found branch, and return its message.

    The page root is a declared branch, so a route that rendered the foreign record
    fails naming the ``content`` branch rather than timing out.
    """
    state = page.navigate_direct(path, page_root, what=what)
    page.require_branch(state, BasePage.BRANCH_ERROR, what)
    message = page.get_error_text()
    assert message, f"{what}: the error display rendered without a message"
    return message


def _assert_absent_from_page(page: BasePage, needles: tuple[str, ...], what: str) -> None:
    """No trace of a foreign record anywhere in the DOM or the document title.

    Only called on a settled branch (``_require_not_found`` returned), so the
    absence is anchored rather than sampled before the route rendered (§D).
    ``page_source`` rather than the visible text: a name in an ``aria-label``, a
    hidden tab panel or a tooltip leaks just the same.
    """
    source = page.driver.page_source
    title = page.driver.title
    for needle in needles:
        assert needle not in source, f"{what}: {needle!r} appears in the page"
        assert needle not in title, f"{what}: {needle!r} appears in the document title"


# -- TC-024-094 ----------------------------------------------------------------


class TestForeignPlantDeepLink:
    """A foreign plant's key in Anna's own tenant reads as "not found" (TC-024-094)."""

    def test_foreign_plant_key_is_indistinguishable_from_a_missing_one(
        self,
        browser: WebDriver,
        base_url: str,
        gardens: tuple[Gardener, Gardener],
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-024-094: Deep-Link auf eine Pflanze eines fremden Tenants zeigt "nicht gefunden".

        Spec: TC-024-094 -- Bernd's plant opened by key in Anna's tenant shows the
        same not-found view as an invented key; its name appears nowhere and
        Anna's own plant list is unchanged.
        """
        anna, bernd = gardens
        name = f"Bernds Tomate {uuid.uuid4().hex[:8]}"
        plant = _create_plant(bernd, name)
        key = plant["key"]

        # API layer of the same probe: 404 (never 403, which would confirm the
        # key exists), and the same key answers for its owner -- otherwise a
        # handler that refuses everything would pass.
        status, payload = _call("GET", f"{anna.tenant_api}/plant-instances/{key}", token=anna.token)
        _expect(status, payload, 404, "Anna reads Bernd's plant through her own tenant")
        assert _read(bernd, f"plant-instances/{key}")["plant_name"] == name
        anna_plants_before = {p["key"] for p in _read(anna, "plant-instances")}
        assert key not in anna_plants_before, "Bernd's plant is listed in Anna's tenant"

        page = PlantInstanceDetailPage(browser, base_url)
        _sign_in(page, anna)
        screenshot("TC-024-094_anna-signed-in", "Anna signed in, her own tenant active")

        foreign_message = _require_not_found(
            page,
            f"{PlantInstanceDetailPage.PATH_PREFIX}/{key}",
            PlantInstanceDetailPage.PAGE,
            "TC-024-094 step 2: Bernd's plant key in Anna's tenant",
        )
        screenshot("TC-024-094_foreign-key-not-found", "Bernd's plant key shows the not-found view")
        _assert_absent_from_page(
            page, (name, plant["instance_id"]), "TC-024-094 step 2: Bernd's plant key"
        )

        missing_message = _require_not_found(
            page,
            f"{PlantInstanceDetailPage.PATH_PREFIX}/{_missing_key()}",
            PlantInstanceDetailPage.PAGE,
            "TC-024-094 step 3: invented plant key",
        )
        screenshot("TC-024-094_missing-key-not-found", "An invented key shows the not-found view")
        assert foreign_message == missing_message, (
            "TC-024-094 FAIL: a foreign key and a missing key must be indistinguishable, "
            f"but the foreign one reads {foreign_message!r} and the missing one {missing_message!r}"
        )

        assert {p["key"] for p in _read(anna, "plant-instances")} == anna_plants_before, (
            "TC-024-094 FAIL: Anna's own plant list changed"
        )
        assert _read(bernd, f"plant-instances/{key}")["plant_name"] == name, (
            "TC-024-094 FAIL: Bernd's plant changed"
        )


# -- TC-024-095 ----------------------------------------------------------------

_LOCATION_FIELDS = ("name", "site_key", "location_type_key", "area_m2")
_TANK_FIELDS = ("name", "tank_type", "volume_liters", "location_key")


class TestForeignDeepLinkEdit:
    """Editing through a foreign deep link changes nothing (TC-024-095)."""

    def test_foreign_location_and_tank_offer_no_form_and_stay_unchanged(
        self,
        browser: WebDriver,
        base_url: str,
        gardens: tuple[Gardener, Gardener],
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-024-095: Bearbeiten ueber einen Deep-Link mit fremdem Schluessel aendert nichts.

        Spec: TC-024-095 -- Bernd's location and tank opened by key in Anna's
        tenant show the not-found view with no form and no save button; direct
        writes with those keys are refused; Bernd sees both objects unchanged.
        """
        anna, bernd = gardens
        sfx = uuid.uuid4().hex[:8]
        site = _create_site(bernd, f"Bernds Garten {sfx}")
        location = _create_location(bernd, site["key"], f"Bernds Gewaechshaus {sfx}")
        tank = _create_tank(bernd, location["key"], f"Bernds Tank {sfx}")
        location_before = _subset(_read(bernd, f"locations/{location['key']}"), _LOCATION_FIELDS)
        tank_before = _subset(_read(bernd, f"tanks/{tank['key']}"), _TANK_FIELDS)

        # The write half of the probe, which the UI below cannot reach because it
        # never renders a form: a direct PUT with Bernd's keys from Anna's tenant.
        status, payload = _call(
            "PUT",
            f"{anna.tenant_api}/locations/{location['key']}",
            token=anna.token,
            body={
                "name": "Hijacked by Anna",
                "site_key": site["key"],
                "location_type_key": "greenhouse",
                "area_m2": 99,
            },
        )
        _expect(status, payload, 404, "Anna updates Bernd's location through her own tenant")
        status, payload = _call(
            "PUT",
            f"{anna.tenant_api}/tanks/{tank['key']}",
            token=anna.token,
            body={"name": "Hijacked by Anna", "volume_liters": 999.0},
        )
        _expect(status, payload, 404, "Anna updates Bernd's tank through her own tenant")

        location_page = LocationDetailPage(browser, base_url)
        tank_page = TankDetailPage(browser, base_url)
        _sign_in(location_page, anna)
        screenshot("TC-024-095_anna-signed-in", "Anna signed in, her own tenant active")

        _require_not_found(
            location_page,
            f"{LocationDetailPage.PATH_PREFIX}/{location['key']}",
            LocationDetailPage.PAGE,
            "TC-024-095 step 1: Bernd's location key in Anna's tenant",
        )
        screenshot("TC-024-095_foreign-location-not-found", "Bernd's location key: not found")
        assert not location_page.is_present(LocationDetailPage.FORM_NAME), (
            "TC-024-095 FAIL: the not-found view for a foreign location renders a filled form"
        )
        assert not location_page.is_present(LocationDetailPage.FORM_SUBMIT), (
            "TC-024-095 FAIL: the not-found view for a foreign location offers a save button"
        )
        _assert_absent_from_page(location_page, (location_before["name"],), "TC-024-095 step 1")

        _require_not_found(
            tank_page,
            f"/standorte/tanks/{tank['key']}",
            TankDetailPage.PAGE,
            "TC-024-095 step 2: Bernd's tank key in Anna's tenant",
        )
        screenshot("TC-024-095_foreign-tank-not-found", "Bernd's tank key: not found")
        assert not tank_page.is_present(TankDetailPage.EDIT_FORM_NAME), (
            "TC-024-095 FAIL: the not-found view for a foreign tank renders a filled form"
        )
        assert not tank_page.is_present(LocationDetailPage.FORM_SUBMIT), (
            "TC-024-095 FAIL: the not-found view for a foreign tank offers a save button"
        )
        _assert_absent_from_page(tank_page, (tank_before["name"],), "TC-024-095 step 2")

        # Step 3: Bernd opens both objects and finds them as he left them.
        _sign_in(location_page, bernd)
        location_page.open(location["key"])
        assert location_before["name"] in location_page.get_title(), (
            "TC-024-095 FAIL: Bernd's location page does not show its name"
        )
        screenshot("TC-024-095_bernd-location-unchanged", "Bernd sees his location unchanged")
        tank_page.open(tank["key"])
        assert tank_before["name"] in tank_page.get_page_title(), (
            "TC-024-095 FAIL: Bernd's tank page does not show its name"
        )
        screenshot("TC-024-095_bernd-tank-unchanged", "Bernd sees his tank unchanged")

        assert _subset(_read(bernd, f"locations/{location['key']}"), _LOCATION_FIELDS) == (
            location_before
        ), "TC-024-095 FAIL: Bernd's location changed"
        assert _subset(_read(bernd, f"tanks/{tank['key']}"), _TANK_FIELDS) == tank_before, (
            "TC-024-095 FAIL: Bernd's tank changed"
        )


# -- TC-024-096 ----------------------------------------------------------------


def _seed_fertilizer(gardener: Gardener) -> dict:
    """The global seed "CalMag", as *gardener*'s tenant lists it.

    Global seed data is a precondition of the E2E stack, not something this test
    can create (only a platform admin writes the shared catalogue), so its
    absence is a loud failure rather than a skip.
    """
    query = urllib.parse.urlencode({"brand": _SEED_FERTILIZER_BRAND, "limit": 200})
    status, rows = _call("GET", f"{gardener.tenant_api}/fertilizers?{query}", token=gardener.token)
    _expect(status, rows, 200, f"{gardener.label} lists the fertilizer catalogue")
    matches = [
        r
        for r in rows
        if r.get("product_name") == _SEED_FERTILIZER_NAME and r.get("origin") == "system"
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected exactly one global seed fertilizer {_SEED_FERTILIZER_NAME!r} "
            f"({_SEED_FERTILIZER_BRAND}) in {gardener.label}'s catalogue, found {len(matches)}. "
            "It is loaded from app/migrations/seed_data/fertilizers.yaml at start-up."
        )
    return matches[0]


class TestGlobalSeedFertilizerIsReadOnly:
    """A grower who is no platform admin cannot change a global seed fertilizer (TC-024-096)."""

    def test_seed_fertilizer_offers_no_save_and_refuses_a_direct_write(
        self,
        browser: WebDriver,
        base_url: str,
        gardens: tuple[Gardener, Gardener],
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-024-096: Globaler Seed-Duenger ist fuer einen Gaertner nicht aenderbar.

        Spec: TC-024-096 -- Anna sees the seed fertilizer read-only (no save
        button, disabled fields); a direct write is refused with 403; the name is
        unchanged for Anna and in Bernd's tenant.
        """
        anna, bernd = gardens
        seed = _seed_fertilizer(anna)
        key, original_name = seed["key"], seed["product_name"]

        # The direct write. It re-sends the stored name on purpose: a broken gate
        # answers 200 here and the test fails, but the shared row other tests read
        # is left exactly as it was.
        status, payload = _call(
            "PUT",
            f"{anna.tenant_api}/fertilizers/{key}",
            token=anna.token,
            body={"product_name": original_name},
        )
        _expect(status, payload, 403, "Anna (no platform admin) writes the global seed fertilizer")

        page = FertilizerDetailPage(browser, base_url)
        _sign_in(page, anna)
        page.open(key)
        screenshot("TC-024-096_seed-fertilizer-detail", "Anna opens the seed fertilizer")
        assert page.is_read_only(), (
            "TC-024-096 FAIL: the global seed fertilizer shows no read-only banner for Anna"
        )
        assert original_name in page.get_page_title_text()

        page.click_tab_edit()
        name_field = page.wait_for_element(FertilizerDetailPage.FORM_PRODUCT_NAME)
        screenshot("TC-024-096_edit-tab-read-only", "Edit tab of the seed fertilizer, read-only")
        assert page.driver.execute_script(
            "return arguments[0].matches(':disabled') || arguments[0].readOnly;", name_field
        ), "TC-024-096 FAIL: the product name of a global seed fertilizer is editable for Anna"
        # Anchored on the name field of the same render pass (§D).
        assert not page.is_present(FertilizerDetailPage.FORM_SUBMIT), (
            "TC-024-096 FAIL: the edit tab of a global seed fertilizer offers a save button"
        )

        page.open(key)
        screenshot("TC-024-096_after-reload", "Seed fertilizer after reload, name unchanged")
        assert original_name in page.get_page_title_text(), (
            "TC-024-096 FAIL: the seed fertilizer's name changed for Anna"
        )
        assert _read(anna, f"fertilizers/{key}")["product_name"] == original_name
        assert _read(bernd, f"fertilizers/{key}")["product_name"] == original_name, (
            "TC-024-096 FAIL: the seed fertilizer's name changed in Bernd's tenant"
        )


# -- TC-024-097 ----------------------------------------------------------------


class TestForeignNutrientPlanPrint:
    """A foreign nutrient plan can be neither opened nor printed (TC-024-097)."""

    def test_foreign_nutrient_plan_shows_not_found_and_offers_no_export(
        self,
        browser: WebDriver,
        base_url: str,
        gardens: tuple[Gardener, Gardener],
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-024-097: Naehrstoffplan eines fremden Tenants ist nicht druckbar.

        Spec: TC-024-097 -- Bernd's plan opened by key in Anna's tenant shows the
        not-found view without an export button; the PDF export with that key is
        404 and carries no trace of the plan, while Bernd can export his own.
        """
        anna, bernd = gardens
        name = f"Bernds Geheimrezept {uuid.uuid4().hex[:8]}"
        plan = _create_nutrient_plan(bernd, name)
        key = plan["key"]

        status, payload = _call("GET", f"{anna.tenant_api}/nutrient-plans/{key}", token=anna.token)
        _expect(status, payload, 404, "Anna reads Bernd's nutrient plan through her own tenant")
        status, raw, _ = _request(
            "GET", f"{anna.tenant_api}/print/nutrient-plan/{key}", token=anna.token
        )
        assert status == 404, f"Anna exports Bernd's nutrient plan: expected 404, got {status}"
        assert name.encode() not in raw, "The refused export still carries the plan name"
        # Positive control: the same export with the owner's own key is a PDF.
        status, raw, content_type = _request(
            "GET", f"{bernd.tenant_api}/print/nutrient-plan/{key}", token=bernd.token
        )
        assert status == 200, f"Bernd exports his own nutrient plan: expected 200, got {status}"
        assert content_type.startswith("application/pdf"), content_type
        assert raw.startswith(b"%PDF"), "Bernd's own export is not a PDF document"

        page = NutrientPlanDetailPage(browser, base_url)
        _sign_in(page, anna)
        screenshot("TC-024-097_anna-signed-in", "Anna signed in, her own tenant active")

        foreign_message = _require_not_found(
            page,
            f"/duengung/plans/{key}",
            NutrientPlanDetailPage.PAGE,
            "TC-024-097 step 1: Bernd's nutrient plan key in Anna's tenant",
        )
        screenshot("TC-024-097_foreign-plan-not-found", "Bernd's plan key: not found, no export")
        assert not page.is_present(PrintButtonPage.PRINT_BUTTON), (
            "TC-024-097 FAIL: the not-found view for a foreign nutrient plan offers the PDF export"
        )
        _assert_absent_from_page(page, (name,), "TC-024-097 step 1")

        missing_message = _require_not_found(
            page,
            f"/duengung/plans/{_missing_key()}",
            NutrientPlanDetailPage.PAGE,
            "TC-024-097: invented nutrient plan key",
        )
        screenshot("TC-024-097_missing-plan-not-found", "An invented plan key: not found")
        assert foreign_message == missing_message, (
            "TC-024-097 FAIL: a foreign plan key and a missing one must read the same, "
            f"got {foreign_message!r} and {missing_message!r}"
        )
        assert _read(bernd, f"nutrient-plans/{key}")["name"] == name, (
            "TC-024-097 FAIL: Bernd's nutrient plan changed"
        )
