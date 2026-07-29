"""Shared helpers for the self-provisioning core-lifecycle journeys (issue #589).

The core-lifecycle journeys (TC-001-079..081, TC-003-046..048, TC-004-089..091,
TC-006-076..077, TC-022-087..088) must never skip at runtime for lack of seed
data — every journey provisions its own preconditions through the real UI.

These helpers centralise the "create a plant instance via the
PlantInstanceCreateDialog" step so each journey can arrange a fresh plant and
then act/assert on it. Creation goes through the actual create dialog (not the
backend API) so the arrange step itself exercises the production UI, matching
the browser-user perspective mandated by NFR-008a.

Beyond provisioning, the module also owns the small pieces of *result
normalisation* and *domain vocabulary* that more than one journey needs (date
parsing, the German watering i18n labels). Those are deliberately not page
objects: they touch no driver, no selector and no wait — they only turn a
rendered string into a comparable value, or name a domain option a page object
resolves for itself.
"""

from __future__ import annotations

import json as _json
import time
import urllib.error as _urlerror
import urllib.request as _urlrequest
from datetime import date, timedelta
from urllib.parse import urlsplit

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException,
)

from .pages.base_page import DE_DATE_RE
from .pages.pflege_dashboard_page import PflegeDashboardPage
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.task_queue_page import TaskQueuePage

# ── Watering domain vocabulary (REQ-004) ─────────────────────────────────────
# German i18n labels (``enums.applicationMethod.drench``,
# ``enums.waterSource.tap``) shared by every watering journey. They are domain
# vocabulary, not selectors — a page object resolves them against the rendered
# options — which is why they live here rather than in any single test module.
DRENCH_OPTION_LABEL = "Gießen"  # dialog option prefix (full: "Gießen (Gießkanne/manuell)")
DRENCH_METHOD_LABEL = "Gießen (Gießkanne/manuell)"  # rendered table cell text
TAP_LABEL = "Leitungswasser"

# Symbolic day tokens a scenario may use instead of a literal date, expressed as
# an offset in days from the browser's own "today".
_DAY_TOKEN_OFFSETS = {"today": 0, "yesterday": -1, "tomorrow": 1}


def parse_de_date(text: str | None) -> tuple[int, int, int] | None:
    """Normalise a German ``d.m.Y`` date out of *text* into ``(day, month, year)``.

    Two different frontend formatters render these cells (``formatDateTime``
    emits '2-digit' parts, ``toLocaleString()`` emits numeric ones), so the
    comparison has to happen on parsed values rather than on the raw strings.
    Returns ``None`` when *text* holds no German date at all.

    This is result normalisation, not user-interface plumbing, which is why it
    belongs to the shared journey support rather than to a page object. The
    pattern itself is :data:`pages.base_page.DE_DATE_RE`, the same one
    ``BasePage.get_browser_today`` uses, so the parse and the reference value can
    never diverge.
    """
    match = DE_DATE_RE.search(text or "")
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def resolve_day_token(token: str, today: tuple[int, int, int]) -> tuple[int, int, int]:
    """Resolve a scenario's day *token* against the browser's *today*.

    Accepts the symbolic tokens ``today``/``yesterday``/``tomorrow`` and a
    literal German ``d.m.Y`` date. Keeping the vocabulary this small is
    deliberate: it is what a declarative scenario needs to state *which* day it
    expects without hard-coding one, and nothing more.

    Args:
        token: The day as written in the scenario, e.g. ``"today"``.
        today: The browser's current ``(day, month, year)``, from
            ``BasePage.get_browser_today``.

    Returns:
        The resolved ``(day, month, year)``.

    Raises:
        ValueError: If *token* is neither a known symbolic token nor a German
            ``d.m.Y`` date — a silent fallback would turn a scenario typo into a
            passing test.
    """
    key = token.strip().lower()
    offset = _DAY_TOKEN_OFFSETS.get(key)
    if offset is not None:
        anchor = date(today[2], today[1], today[0]) + timedelta(days=offset)
        return anchor.day, anchor.month, anchor.year
    literal = parse_de_date(token)
    if literal is None:
        raise ValueError(
            f"Unknown day token {token!r}: expected one of "
            f"{sorted(_DAY_TOKEN_OFFSETS)} or a German d.m.Y date"
        )
    return literal


def unique_suffix() -> str:
    """Return a short, run-unique numeric suffix.

    Uses millisecond wall-clock time so repeated runs against the same
    persistent tenant never collide on instance ids (the seed DB survives
    between sessions — idempotency requirement).
    """
    return f"{int(time.time() * 1000) % 1_000_000:06d}"


def provision_plant(
    list_page: PlantInstanceListPage,
    *,
    id_prefix: str,
    plant_name: str | None = None,
    phase_index: int | None = None,
    species_query: str = "a",
) -> tuple[str, str]:
    """Create a plant instance through the create dialog and return ``(key, instance_id)``.

    Selects the first species matching *species_query* from the autocomplete,
    optionally sets a display name and a start phase (``phase_index`` into the
    current-phase select — e.g. ``-2`` for a late 'Ist-Stand' start), assigns a
    unique instance id derived from *id_prefix*, submits, then locates the new
    row by searching for the unique instance id and navigates to its detail
    page. The browser is left on the plant detail page.

    Raising (never skipping) on failure is deliberate: the journey's whole point
    is that the core path always runs.
    """
    instance_id = f"{id_prefix}-{unique_suffix()}"

    list_page.open()
    list_page.click_create()
    list_page.select_species(species_query)
    if plant_name is not None:
        list_page.fill_plant_name(plant_name)
    if phase_index is not None:
        list_page.select_current_phase_by_index(phase_index)
    list_page.set_instance_id(instance_id)
    list_page.submit_create_form()
    list_page.wait_for_loading_complete()

    # Locate exactly this plant by its unique instance id.
    list_page.search(instance_id)
    list_page.wait_for_loading_complete()
    if list_page.get_row_count() == 0:
        raise AssertionError(
            f"Self-provisioning failed: plant instance '{instance_id}' did not "
            f"appear in the list after creation"
        )
    # Await a URL that is *different* from the one being left, not merely one
    # matching the detail route. `wait_for_url_contains` would be satisfied at
    # once whenever a previous test left the browser on some plant's detail page,
    # and the key read back would be that plant's — silently provisioning one
    # plant and returning another's identity (#835).
    before = list_page.driver.current_url
    list_page.click_row(0)
    url = list_page.wait_for_url_change(before, "/pflanzen/plant-instances/")
    # Path only. The list's search term survives the navigation as `?q=…`, so
    # splitting the raw URL yielded keys like `53490?q=JOURNEY-004X-936182`,
    # which the backend then 404'd on. Before #835 this was invisible: the
    # post-condition returned the URL being *left*, which carried no query.
    key = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]

    # Confirm the page we landed on is the plant we just created, before any
    # journey builds 60 lines of assertions on `key`. Every wrong-plant failure
    # #835 uncovered surfaced far downstream — as a chip pointing at a stranger,
    # or a 404 on a care profile — where the real cause was unrecognisable. This
    # is the cheap place to notice, and it fails loudly.
    if not list_page.page_shows_text(instance_id):
        raise AssertionError(
            f"Self-provisioning landed on {url!r} (key={key!r}), which does not "
            f"show '{instance_id}'. The row click opened a different plant — do "
            f"not trust this key."
        )
    return key, instance_id


def create_care_task(
    task_queue: TaskQueuePage,
    instance_id: str,
    task_name: str,
    *,
    category: str = "care_reminder",
    priority: str = "high",
) -> str:
    """Create a care task for plant *instance_id* via the queue dialog and return its key.

    Drives the real TaskCreateDialog (category ``care_reminder``, due today,
    high priority, plant selected by its unique instance id), submits, then
    locates the new card in the queue by its unique *task_name*.

    Raising (never skipping) on a missing card is deliberate: a self-provisioning
    test must always establish its own precondition.

    .. warning::

       The ``due today`` + ``priority="high"`` combination is **load-bearing for
       another test's stability**, not cosmetic. A due-today task lands in the
       queue's ``today`` urgency group, which renders at (or very near) the head
       of the shared ``mein-garten`` queue. Any test that grabs "the first task"
       and then *mutates* it therefore mutates whatever task this helper created
       last. That was the cause of the cross-test interference tracked in
       **issue #791**: ``test_req006_task_queue.py::TestTaskQueueQuickActions``
       started, completed and skipped ``get_task_keys()[0]``, so TC-REQ-022-038
       found its own task already ``in_progress``. Those three tests now
       self-provision, but the coupling itself still exists for any future
       queue-head mutator, and changing these defaults, the due date, or the
       queue's ordering shifts it: re-check #791 and the queue-head consumers
       (``get_task_keys()``, ``get_first_task_card()``) before you do.
    """
    # Fill and submit the create dialog. Under heavy parallel load (xdist) the
    # queue behind the dialog can render slowly enough to delay a dialog field
    # beyond its wait, or intercept a click; retry the whole dialog several
    # times before giving up. Each attempt re-navigates (task_queue.open), which
    # dismisses any half-open dialog from a previous failed attempt.
    last_exc: Exception | None = None
    for _attempt in range(4):
        try:
            task_queue.open()
            task_queue.click_create_task()
            # Confirm the dialog is actually interactive (its first field is
            # present) before driving the remaining fields — the MUI Dialog can
            # be in the DOM/visible while its form is still mounting under load.
            task_queue.wait_for_element_visible(task_queue.FORM_NAME)
            task_queue.fill_task_name(task_name)
            task_queue.select_task_category(category)
            task_queue.set_due_date_today()
            task_queue.select_task_priority(priority)
            if not task_queue.select_task_plant_by_text(instance_id):
                raise AssertionError(
                    f"Self-provisioning failed: plant '{instance_id}' offered no "
                    f"option in the task-create plant autocomplete"
                )
            task_queue.submit_task_form()
            task_queue.wait_for_loading_complete()
            break
        except (
            TimeoutException,
            ElementClickInterceptedException,
            ElementNotInteractableException,
            StaleElementReferenceException,
        ) as exc:
            last_exc = exc
            time.sleep(1.5)
    else:
        raise AssertionError(
            f"Self-provisioning failed: could not drive the task-create dialog "
            f"for '{task_name}' after 4 attempts: {last_exc}"
        )

    # The queue refetches after the mutation; poll a few reloads so a slow
    # refetch does not read the list before the new card is materialised.
    deadline = time.time() + 15.0
    while time.time() < deadline:
        task_queue.open()
        key = task_queue.find_task_key_by_name(task_name)
        if key is not None:
            return key
        time.sleep(1.0)
    raise AssertionError(
        f"Self-provisioning failed: care task '{task_name}' did not appear "
        f"in the queue after creation"
    )


def _api_request(
    url: str,
    method: str,
    token: str | None = None,
    data: dict | None = None,
) -> tuple[int, dict]:
    """Minimal JSON HTTP helper mirroring conftest's ``_api_helpers`` (optional Bearer).

    Kept self-contained (no conftest import) so the journey helpers stay a leaf
    module; the shape matches the seed fixture's urllib usage.
    """
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = _json.dumps(data).encode() if data is not None else None
    req = _urlrequest.Request(url, data=body, headers=headers, method=method)
    try:
        with _urlrequest.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return resp.status, (_json.loads(raw) if raw else {})
    except _urlerror.HTTPError as exc:
        try:
            return exc.code, _json.loads(exc.read())
        except Exception:
            return exc.code, {}


def provision_watering_care_task(base_url: str, seed: dict, plant_key: str) -> None:
    """Self-provision the TC-004-092 precondition on the backend for *plant_key*.

    Ensures the plant has a **persisted care profile with**
    ``auto_create_watering_task`` **and exactly one pending** ``— watering``
    **task** in its task history — the mandatory precondition for the
    WateringLog→task coupling (``advance_watering_task_after_log``) to complete
    the open watering task and schedule the follow-up. Without an open task that
    coupling is a no-op and the watering only shows in the two log views (the
    Guard called out in the spec).

    Three steps, each idempotent:

    1. ``GET /care-reminders/plants/{key}/profile`` — the get-or-create route
       *persists* a default profile (``auto_create_watering_task`` defaults to
       ``True``) so the generator can see it.
    2. ``PATCH …/profile`` — assert ``auto_create_watering_task`` is on
       explicitly (belt-and-suspenders against a future default change).
    3. ``POST /t/{slug}/tasks/generate-care-reminders`` — materialise exactly one
       pending ``— watering`` task for the plant (runs the daily producer eagerly
       in-process).

    Raising (never skipping) on failure is deliberate: the test's whole point is
    that the cross-view path always runs (NFR-008a self-provisioning).
    """
    # Fresh token: the session-seed JWT expires after 15 min — long before a
    # late-scheduled test runs (led to 401 self-provisioning failures here).
    from .conftest import _fresh_access_token

    token = _fresh_access_token(seed, base_url)
    slug = seed.get("tenant_slug", "mein-garten")
    api = base_url.rstrip("/") + "/api/v1"

    status, _ = _api_request(f"{api}/care-reminders/plants/{plant_key}/profile", "GET", token)
    if status not in (200, 201):
        raise AssertionError(
            f"Self-provisioning failed: could not create a care profile for "
            f"'{plant_key}' (status={status})"
        )

    _api_request(
        f"{api}/care-reminders/plants/{plant_key}/profile",
        "PATCH",
        token,
        {"auto_create_watering_task": True},
    )

    gen_status, _ = _api_request(f"{api}/t/{slug}/tasks/generate-care-reminders", "POST", token, {})
    if gen_status not in (200, 201):
        raise AssertionError(
            f"Self-provisioning failed: generate-care-reminders returned "
            f"status={gen_status} for tenant '{slug}'"
        )


def wait_for_watering_card(
    pflege: PflegeDashboardPage,
    plant_key: str,
    timeout: float = 15.0,
) -> bool:
    """Wait for the plant's live watering care card to render on ``/pflege``.

    A freshly provisioned plant gets an auto care profile whose watering entry
    is due today, so the merged care dashboard renders the
    ``care-card-care-{plant_key}-watering`` card on its own — no explicit
    "Generate reminders" click (which would materialise a task and deduplicate
    the live card away). Returns True once the card appears within *timeout*.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        pflege.open()
        if pflege.has_care_card(plant_key, "watering"):
            return True
        time.sleep(1.0)
    return False
