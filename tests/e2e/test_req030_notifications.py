"""E2E tests for REQ-030 — Multi-Kanal-Benachrichtigungssystem.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-030.md):
  TC-REQ-030-001  ->  TC-REQ-030-009  Notification-Einstellungs-Tab in Kontoeinstellungen navigieren
  TC-REQ-030-002  ->  TC-REQ-030-010  Kanalverwaltung -- Uebersicht aller Kanaele
  TC-REQ-030-003  ->  TC-REQ-030-013  E-Mail-Kanal aktivieren und E-Mail-Adresse eintragen
  TC-REQ-030-004  ->  TC-006-082  Aufgabe neu zuweisen -- Zuweisungs-Benachrichtigung (Soll)
  TC-REQ-030-005  ->  TC-006-083  Aufgabe bearbeiten -- Benachrichtigung synchron aktualisiert (Soll)
  TC-REQ-030-006  ->  TC-006-084  Aufgabe loeschen -- veraltete Benachrichtigung entfernt (Soll)
  TC-REQ-030-007  ->  TC-006-085  Aufgabe abschliessen -- Faellig-Benachrichtigung erledigt (Soll)
  TC-REQ-030-008  ->  TC-022-093  Giesszyklus-Anpassung -- Benachrichtigung synchron verschoben (Soll)
  TC-REQ-030-009  ->  TC-022-094  Erinnerung bestaetigen -- Benachrichtigung als erledigt markiert (Soll)
  TC-REQ-030-010  ->  TC-REQ-030-063  Quell-Aufgabe verschoben -- Benachrichtigung zeigt neue Faelligkeit (Soll)
  TC-REQ-030-011  ->  TC-REQ-030-064  Quell-Aufgabe abgeschlossen -- Benachrichtigung erledigt (Soll)
  TC-REQ-030-012  ->  TC-REQ-030-065  Quell-Aufgabe geloescht -- verwaiste Benachrichtigung entfernt (Soll)
  TC-REQ-030-013  ->  TC-REQ-030-066  Giesszyklus angepasst -- care.watering neu terminiert, kein Duplikat (Soll)
  TC-REQ-030-014  ->  TC-REQ-030-067  Actionable 'Erledigt'-Button schliesst Quelle und markiert (Soll)

Scope: Smoke-Coverage des Notification-Settings-Workflows (REQ-030 §5.4) plus
die Soll-Verhalten-Rueckkopplung Quelle -> Benachrichtigung (REQ-030 §4.2/§5.2).
Out of scope: Test-Send-Buttons, echte Zustellung.

Hinweis zu den Rueckkopplungs-Tests (TC-REQ-030-004..014): REQ-030 §4.2 fordert,
dass eine Aenderung der Quelle (Aufgabe/Care-Erinnerung verschoben, abgeschlossen,
geloescht oder Zyklus angepasst) die zugehoerige Benachrichtigung synchron
aktualisiert. Seit Issue #742 ist diese Kopplung implementiert
(``NotificationPropagationService`` verdrahtet in Task-/Care-Service) und der
Actionable-"Erledigt"-Button bestaetigt die Quelle in einem Schritt (§4.2), daher
laufen diese Tests jetzt als regulaere Faelle (kein xfail mehr).
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import (
    LoginPage,
    NotificationSettingsPage,
    PflegeDashboardPage,
    TaskDetailPage,
    TaskQueuePage,
)
from .pages.notification_center_page import NotificationCenterPage
from ._auth_helpers import clear_auth_session

pytestmark = pytest.mark.requires_auth

# Issue #742 — the synchronous source→notification feedback loop (REQ-030 §4.2/
# §5.2) is now implemented: task/care mutations propagate into the in-app
# notification centre, and an actionable "Done" button confirms the source in one
# step. The tests below therefore drive the real flow (no longer xfail).

# -- Demo credentials (full mode -- see conftest.DEMO_EMAIL_FULL) ------------
DEMO_EMAIL = "demo@kamerplanter.example"
DEMO_PASSWORD = "demo-passwort-2024"


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def login_page(browser: WebDriver, base_url: str) -> LoginPage:
    """Return a LoginPage bound to the test browser."""
    return LoginPage(browser, base_url)


@pytest.fixture
def notif_page(browser: WebDriver, base_url: str) -> NotificationSettingsPage:
    """Return a NotificationSettingsPage bound to the test browser."""
    return NotificationSettingsPage(browser, base_url)


@pytest.fixture
def notif_center(browser: WebDriver, base_url: str) -> NotificationCenterPage:
    """Return a NotificationCenterPage (bell + drawer) bound to the test browser."""
    return NotificationCenterPage(browser, base_url)


@pytest.fixture
def task_queue(browser: WebDriver, base_url: str) -> TaskQueuePage:
    """Return a TaskQueuePage bound to the test browser."""
    return TaskQueuePage(browser, base_url)


@pytest.fixture
def task_detail(browser: WebDriver, base_url: str) -> TaskDetailPage:
    """Return a TaskDetailPage bound to the test browser."""
    return TaskDetailPage(browser, base_url)


@pytest.fixture
def pflege(browser: WebDriver, base_url: str) -> PflegeDashboardPage:
    """Return a PflegeDashboardPage bound to the test browser."""
    return PflegeDashboardPage(browser, base_url)


def _ensure_logged_in(login_page: LoginPage) -> None:
    """Log in as the demo user.  Mirrors test_req023_account_settings."""
    clear_auth_session(login_page.driver)
    login_page.open()
    login_page.login(DEMO_EMAIL, DEMO_PASSWORD)
    login_page.wait_for_url_contains("/dashboard")


def _drawer_notification_texts(notif_center: NotificationCenterPage) -> list[str]:
    """Open the drawer and return the visible text of every notification card."""
    notif_center.open_drawer()
    return [notif_center.get_notification_text(k) for k in notif_center.get_notification_keys()]


def _poll_own_notifications_done(
    notif_center: NotificationCenterPage, task_name: str, timeout: float = 12.0
) -> list[str]:
    """Reload + poll until every own notification is done (or timeout).

    The propagation is synchronous server-side, but the drawer only refetches
    on a fresh open — reload per attempt so every read is a fresh fetch.
    Done-signal is the card's UNREAD state ("Erledigt" in the card TEXT is the
    actionable done-BUTTON, i.e. present exactly while the notification is
    still open — the opposite of a done marker). Returns the still-unread own
    card texts (empty list = success).
    """
    import time as _t

    deadline = _t.time() + timeout
    unread_own: list[str] = []
    while _t.time() < deadline:
        notif_center.driver.refresh()
        notif_center.open_drawer()
        own_keys = [
            k
            for k in notif_center.get_notification_keys()
            if task_name in notif_center.get_notification_text(k)
        ]
        unread_own = [
            notif_center.get_notification_text(k) for k in own_keys if notif_center.is_unread(k)
        ]
        if not unread_own:
            return []
        _t.sleep(1.0)
    return unread_own


def _first_care_ids(pflege: PflegeDashboardPage) -> tuple[str, str]:
    """Return (plant_key, reminder_type) of the first care card, or skip."""
    cards = pflege.get_all_care_cards()
    if not cards:
        pytest.skip("No care cards available -- seed dependent")
    testid = cards[0].get_attribute("data-testid") or ""
    suffix = testid.replace("care-card-care-", "")
    parts = suffix.rsplit("-", 1)
    if len(parts) < 2:
        pytest.skip(f"Unexpected card testid format: {testid}")
    return parts[0], parts[1]


# -- Self-provisioning helpers (e2e-test-stability §A) ------------------------
#
# The seven tests below used to mutate/assert on ``task_queue.get_task_keys()
# [0]`` -- a shared session-seeded task raced by every parallel xdist worker
# (each worker's own session fixture recreates the same-named seeds). Instead
# each test now provisions its own uniquely named entity and scopes every
# notification assertion to that entity, per §A/§B of e2e-test-stability.


def _own_user_key(e2e_seed_data: dict, base_url: str) -> str:
    """Return the acting user's own ``user_key`` via ``GET /api/v1/users/me``.

    Used by the reassignment test so 'Zugewiesen an' targets a real,
    resolvable key (the viewer itself) instead of a foreign literal string the
    acting user has no visibility into -- Issue #742/#752: the assignment
    notification is delivered to ``task.assigned_to_user_key``, not to the
    user performing the reassignment.
    """
    from .conftest import _api_helpers, _fresh_access_token

    _, get = _api_helpers(_fresh_access_token(e2e_seed_data, base_url))
    status, resp = get(f"{base_url.rstrip('/')}/api/v1/users/me")
    if status != 200 or not isinstance(resp, dict) or not resp.get("key"):
        pytest.fail(
            "Could not resolve the acting user's own user_key via "
            f"GET /api/v1/users/me: status={status}, resp={resp}"
        )
    return resp["key"]


def _create_e2e_task(
    e2e_seed_data: dict,
    base_url: str,
    *,
    due_in_days: int = 1,
    category: str = "maintenance",
    priority: str = "medium",
) -> tuple[str, str]:
    """Create a uniquely named, self-provisioned task via the API.

    Self-Provisioning per e2e-test-stability §A: pattern ``E2E-N030-<hex8>``,
    collision-free across parallel workers and repeated runs. Returns
    ``(task_key, task_name)``.
    """
    from .conftest import _e2e_api_post

    task_name = f"E2E-N030-{uuid.uuid4().hex[:8]}"
    due_date = (date.today() + timedelta(days=due_in_days)).isoformat()
    status, resp = _e2e_api_post(
        e2e_seed_data,
        base_url,
        "tasks",
        {
            "name": task_name,
            "name_de": task_name,
            "category": category,
            "priority": priority,
            "due_date": due_date,
        },
    )
    if status != 201 or not isinstance(resp, dict) or not resp.get("key"):
        pytest.fail(f"Self-provisioning failed: POST tasks -> {status}: {resp}")
    return resp["key"], task_name


def _care_notification_key(
    notif_center: NotificationCenterPage, plant_name: str, reminder_type: str
) -> str | None:
    """Return the drawer notification key matching this plant + reminder type.

    Care notifications carry the plant's display name as their title and the
    reminder type inside their body (``NotificationPropagationService.
    sync_care_notification``); this scopes lookups to the specific plant
    instead of the shared demo account's global unread badge, which every
    parallel xdist worker mutates concurrently. Requires the drawer to
    already be open.
    """
    for key in notif_center.get_notification_keys():
        text = notif_center.get_notification_text(key)
        if plant_name and plant_name in text and reminder_type in text.lower():
            return key
    return None


# -- TC-REQ-030-001: Navigate to notification settings tab -------------------


class TestNotificationSettingsNavigation:
    """Notification settings tab navigation (Spec: TC-REQ-030-009)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_notification_tab_loads(
        self,
        login_page: LoginPage,
        notif_page: NotificationSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-009: Notification settings tab opens and renders the save button.

        Spec: TC-REQ-030-009 -- Notification-Einstellungs-Tab in Kontoeinstellungen
        navigieren.
        """
        _ensure_logged_in(login_page)
        notif_page.open()
        screenshot(
            "TC-REQ-030-001_notification-tab-loaded",
            "Notification settings tab after initial load",
        )

        tab_labels = notif_page.get_tab_labels()
        assert any("benachrichtigung" in label.lower() for label in tab_labels), (
            f"TC-REQ-030-001 FAIL: Expected 'Benachrichtigungen' tab, got: {tab_labels}"
        )

        # Save button is the anchor element rendered by NotificationSettingsTab.
        assert notif_page.is_save_button_visible(), (
            "TC-REQ-030-001 FAIL: Expected notification-settings-save button to be visible"
        )


# -- TC-REQ-030-002: Channel overview ----------------------------------------


class TestNotificationChannelOverview:
    """Channel toggle overview (Spec: TC-REQ-030-010)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_all_four_channels_rendered(
        self,
        login_page: LoginPage,
        notif_page: NotificationSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-010: All four delivery channels render with toggles.

        Spec: TC-REQ-030-010 -- Kanalverwaltung -- Uebersicht aller Kanaele.

        REQ-030 ships home_assistant, email, pwa and apprise.  Visibility may
        be filtered by experience level (REQ-021) -- on the demo account at
        least home_assistant and email MUST be visible at any expertise level.
        """
        _ensure_logged_in(login_page)
        notif_page.open()
        screenshot(
            "TC-REQ-030-002_channel-overview",
            "Notification channel overview with toggles",
        )

        visible = notif_page.get_visible_channel_keys()

        # FIXME: REQ-021 may hide apprise/pwa for beginner users.  We assert
        # the two always-visible channels plus a sane minimum count instead
        # of all four.
        assert "home_assistant" in visible, (
            f"TC-REQ-030-002 FAIL: Expected 'home_assistant' channel toggle, got: {visible}"
        )
        assert "email" in visible, (
            f"TC-REQ-030-002 FAIL: Expected 'email' channel toggle, got: {visible}"
        )
        assert len(visible) >= 2, (
            f"TC-REQ-030-002 FAIL: Expected at least 2 channels, got: {visible}"
        )


# -- TC-REQ-030-003: Enable email channel + persist --------------------------


class TestNotificationEmailChannelEnable:
    """Enable email channel and configure address (Spec: TC-REQ-030-013)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_enable_email_channel_and_save(
        self,
        login_page: LoginPage,
        notif_page: NotificationSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-013: Enable email channel, type address, save and verify.

        Spec: TC-REQ-030-013 -- E-Mail-Kanal aktivieren und E-Mail-Adresse
        eintragen.

        We deliberately do NOT trigger the test-send button -- the test only
        exercises the configuration workflow, not real delivery.  The test
        is idempotent: it always sets the same email value and toggles the
        channel ON, so re-runs converge.
        """
        _ensure_logged_in(login_page)
        notif_page.open()
        screenshot(
            "TC-REQ-030-003_before-enable-email",
            "Notification settings before enabling email channel",
        )

        # Activate email channel (idempotent — only flips when needed).
        notif_page.set_channel_enabled("email", enabled=True)

        # Conditional config field appears once the switch is on.
        target_address = "demo+e2e@kamerplanter.example"
        notif_page.set_email_address(target_address)
        screenshot(
            "TC-REQ-030-003_email-channel-configured",
            "Email channel enabled with test address filled",
        )

        notif_page.save()

        # Persistence check 1: success snackbar appears.
        snackbar_text = notif_page.wait_for_success_snackbar()
        assert snackbar_text, (
            "TC-REQ-030-003 FAIL: Expected success snackbar after saving notification settings"
        )

        # Persistence check 2: reload tab and verify the toggle + address persisted.
        notif_page.open()
        screenshot(
            "TC-REQ-030-003_email-channel-after-reload",
            "Notification settings after reload — email channel persisted",
        )
        assert notif_page.is_channel_enabled("email"), (
            "TC-REQ-030-003 FAIL: Email channel toggle did not persist across reload"
        )
        assert notif_page.get_email_address() == target_address, (
            f"TC-REQ-030-003 FAIL: Expected email '{target_address}' to persist, "
            f"got: '{notif_page.get_email_address()}'"
        )


# -- TC-006-082 to TC-006-085: Task-Update -> Notification Feedback (Soll) ----


class TestTaskUpdateNotificationFeedback:
    """Task mutations propagate into notifications (TC-006-082..085).

    These exercise the REQ-030 §4.2 feedback loop implemented in Issue #742: each
    test drives the full real flow (open notification centre, mutate the source
    task, re-inspect the notification centre).
    """

    @pytest.mark.requires_auth
    def test_reassign_task_delivers_assignment_notification(
        self,
        login_page: LoginPage,
        task_detail: TaskDetailPage,
        notif_center: NotificationCenterPage,
        base_url: str,
        e2e_seed_data: dict,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-006-082: Reassigning a task delivers an assignment notification.

        Spec: TC-006-082 -- Aufgabe neu zuweisen -- 'Meine Aufgaben'-Filter und
        Benachrichtigung folgen der Zuweisung.

        Abweichung Spec vs. Impl: ein 'Meine Aufgaben'-Filter existiert im
        Frontend nicht; die Neuzuweisung via ``set_assigned_to`` ist setzbar und
        liefert dem neu zugewiesenen Mitglied eine Assignment-Benachrichtigung
        (Issue #742). Self-provisioned own task, reassigned to the acting
        user's own ``user_key`` (Issue #752: the previous version reassigned
        to the literal string ``"e2e-grower"``, a non-existent user the demo
        viewer could never see a notification for) -- identical in both app
        modes, so the assertion no longer depends on the light/full split.
        """
        _ensure_logged_in(login_page)
        own_key = _own_user_key(e2e_seed_data, base_url)
        task_key, task_name = _create_e2e_task(e2e_seed_data, base_url)

        task_detail.open(task_key)
        task_detail.open_edit_tab()
        task_detail.set_assigned_to(own_key)
        task_detail.save_edit()
        screenshot(
            "TC-REQ-030-004_after-reassign",
            f"Task {task_key} reassigned to the acting user",
        )

        texts = _drawer_notification_texts(notif_center)
        screenshot(
            "TC-REQ-030-004_notification-center",
            "Notification centre after reassignment",
        )

        own_matches = [t for t in texts if task_name in t]
        assert own_matches and any(
            "zugewiesen" in t.lower() or "assign" in t.lower() for t in own_matches
        ), (
            "TC-REQ-030-004 FAIL (Soll): Expected an assignment notification for the "
            f"reassigned task '{task_name}', got matches: {own_matches}"
        )

    @pytest.mark.requires_auth
    def test_edit_task_updates_existing_notification(
        self,
        login_page: LoginPage,
        task_detail: TaskDetailPage,
        notif_center: NotificationCenterPage,
        base_url: str,
        e2e_seed_data: dict,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-006-083: Editing a task updates its existing due-notification in place.

        Spec: TC-006-083 -- Aufgabe bearbeiten -- zugehoerige Benachrichtigung
        wird synchron aktualisiert (kein Duplikat, kein veralteter Termin).

        Self-provisioned own task (e2e-test-stability §A) -- a shared seed
        task could be renamed/reassigned/deleted by the reassign/delete/
        complete tests on a different xdist worker between this test's read
        and its assertion.
        """
        _ensure_logged_in(login_page)
        task_key, task_name = _create_e2e_task(e2e_seed_data, base_url)
        screenshot(
            "TC-REQ-030-005_before-edit",
            f"Task {task_key} before edit",
        )

        new_name = f"{task_name} -- verschoben"
        target_due = (date.today() + timedelta(days=3)).isoformat()
        task_detail.open(task_key)
        task_detail.open_edit_tab()
        task_detail.set_name(new_name)
        task_detail.set_due_date(target_due)
        task_detail.save_edit()

        texts = _drawer_notification_texts(notif_center)
        screenshot(
            "TC-REQ-030-005_after-edit",
            "Notification centre after editing task name + due date",
        )

        own_matches = [t for t in texts if task_name in t]
        assert own_matches and any("verschoben" in t.lower() for t in own_matches), (
            "TC-REQ-030-005 FAIL (Soll): Expected the due-notification for "
            f"'{task_name}' to reflect the updated title '{new_name}', got "
            f"matches: {own_matches}"
        )

    @pytest.mark.requires_auth
    def test_delete_task_removes_stale_notification(
        self,
        login_page: LoginPage,
        task_detail: TaskDetailPage,
        notif_center: NotificationCenterPage,
        base_url: str,
        e2e_seed_data: dict,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-006-084: Deleting a task removes its stale due-notification.

        Spec: TC-006-084 -- Aufgabe loeschen -- veraltete Benachrichtigung wird
        entfernt und nicht mehr als ungelesen gezaehlt.

        Self-provisioned own task (e2e-test-stability §A). The unread-badge
        assertion is dropped in favour of an item-scoped existence check: the
        badge is the shared demo account's global unread count, mutated
        concurrently by every parallel xdist worker's own tests, so an exact
        delta is not a valid signal (§B) -- the notification disappearing
        entirely is the strictly stronger, item-scoped proof of removal.
        """
        _ensure_logged_in(login_page)
        task_key, task_name = _create_e2e_task(e2e_seed_data, base_url)

        pre_texts = _drawer_notification_texts(notif_center)
        assert any(task_name in t for t in pre_texts), (
            f"Setup invariant: expected task '{task_name}' to already have a "
            f"due-notification before deletion, got: {pre_texts}"
        )
        notif_center.close_drawer()
        screenshot(
            "TC-REQ-030-006_before-delete",
            f"Notification centre before deleting task {task_key}",
        )

        task_detail.open(task_key)
        task_detail.delete_task()

        texts = _drawer_notification_texts(notif_center)
        screenshot(
            "TC-REQ-030-006_after-delete",
            "Notification centre after deleting task",
        )

        assert not any(task_name in t for t in texts), (
            "TC-REQ-030-006 FAIL (Soll): Expected the stale notification for the deleted "
            f"task '{task_name}' to be removed, got matches: "
            f"{[t for t in texts if task_name in t]}"
        )

    @pytest.mark.requires_auth
    def test_complete_task_marks_notification_done(
        self,
        login_page: LoginPage,
        task_queue: TaskQueuePage,
        notif_center: NotificationCenterPage,
        base_url: str,
        e2e_seed_data: dict,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-006-085: Completing a task auto-marks its due-notification done.

        Spec: TC-006-085 -- Aufgabe abschliessen -- offene Faellig-Benachrichtigung
        wird als erledigt markiert (nicht mehr im ungelesen-Badge).
        """
        _ensure_logged_in(login_page)
        # Self-provisioned task (e2e-test-stability §A): due today so the
        # creation propagates an unread due-notification we can then watch.
        task_key, task_name = _create_e2e_task(e2e_seed_data, base_url, due_in_days=0)

        notif_center.open_drawer()
        texts_before = _drawer_notification_texts(notif_center)
        if not any(task_name in t for t in texts_before):
            pytest.fail(
                "TC-REQ-030-007 precondition: expected an unread due-notification "
                f"for the fresh task '{task_name}', got: {texts_before}"
            )
        notif_center.close_drawer()
        screenshot(
            "TC-REQ-030-007_before-complete",
            f"Notification centre before completing task {task_key}",
        )

        task_queue.open()
        task_queue.complete_task(task_key)
        task_queue.wait_for_loading_complete()

        own_after = _poll_own_notifications_done(notif_center, task_name)
        screenshot(
            "TC-REQ-030-007_after-complete",
            "Notification centre after completing the task",
        )

        assert not own_after, (
            "TC-REQ-030-007 FAIL (Soll): Expected completing the task to mark its "
            f"due-notification done/read; still unread: {own_after}"
        )


# -- TC-022-093 / TC-022-094: Care -> Notification Feedback (Soll) ------------


class TestCareNotificationFeedback:
    """Care-cycle changes should propagate into notifications (Soll: TC-022-093/094)."""

    @pytest.mark.requires_auth
    def test_interval_change_reschedules_watering_notification(
        self,
        login_page: LoginPage,
        pflege: PflegeDashboardPage,
        notif_center: NotificationCenterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-093: Lengthening the watering interval reschedules the notification.

        Spec: TC-022-093 -- Giesszyklus-Anpassung -- faellige Benachrichtigung wird
        synchron auf den neuen Termin verschoben (kein Duplikat).
        """
        _ensure_logged_in(login_page)
        pflege.open()
        if pflege.get_care_card_count() == 0:
            pytest.skip("No care reminders available -- seed dependent")

        plant_key, _ = _first_care_ids(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()
        if not pflege.is_present(PflegeDashboardPage.WATERING_INTERVAL_SLIDER):
            pytest.skip("Watering task not enabled on this profile -- no interval slider")
        screenshot(
            "TC-REQ-030-008_before-interval-change",
            f"Care profile for {plant_key} before lengthening the watering interval",
        )
        pflege.set_watering_interval(14)
        pflege.click_save_profile()
        pflege.wait_for_loading_complete()

        texts = _drawer_notification_texts(notif_center)
        screenshot(
            "TC-REQ-030-008_after-interval-change",
            "Notification centre after lengthening the watering interval",
        )

        assert any(
            any(term in t.lower() for term in ("gieß", "gie", "water", "wasser")) for t in texts
        ), (
            "TC-REQ-030-008 FAIL (Soll): Expected the care.watering notification to "
            f"follow the new 14-day cycle, got: {texts}"
        )

    @pytest.mark.requires_auth
    def test_confirm_reminder_marks_notification_done(
        self,
        login_page: LoginPage,
        pflege: PflegeDashboardPage,
        notif_center: NotificationCenterPage,
        base_url: str,
        e2e_seed_data: dict,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-094: Confirming a reminder auto-marks its notification done.

        Spec: TC-022-094 -- Erinnerung bestaetigen -- zugehoerige Benachrichtigung
        wird als erledigt markiert (nicht mehr im ungelesen-Badge).

        Uses the shared care-reminder seed (read-only lookup, permitted by
        e2e-test-stability §A) but scopes the done-assertion to that specific
        plant/reminder-type notification instead of the account-wide unread
        badge -- the badge is global state shared by every parallel xdist
        worker (all full-mode tests log in as the same demo user), so an
        exact before/after delta is not a valid per-test signal (§B).
        """
        _ensure_logged_in(login_page)
        pflege.open()
        plant_key, reminder_type = _first_care_ids(pflege)
        # Resolve the plant's display name via the API: the notification body
        # carries the plant *name*, while the card's visible subtitle is the
        # care type (get_card_plant_name returned 'Umtopfen' here).
        from .conftest import _api_helpers, _fresh_access_token

        _, _get = _api_helpers(_fresh_access_token(e2e_seed_data, base_url))
        slug = e2e_seed_data.get("tenant_slug", "mein-garten")
        status, plant = _get(f"{base_url.rstrip('/')}/api/v1/t/{slug}/plant-instances/{plant_key}")
        plant_name = (
            (plant.get("name") or "").strip() if status == 200 and isinstance(plant, dict) else ""
        )
        if not plant_name:
            pytest.skip(f"Could not resolve plant name for key {plant_key} (status={status})")

        notif_center.open_drawer()
        notif_key = _care_notification_key(notif_center, plant_name, reminder_type)
        if notif_key is None:
            pytest.skip(
                f"No in-app notification found for plant '{plant_name}' / "
                f"reminder '{reminder_type}' -- seed dependent"
            )
        was_unread = notif_center.is_unread(notif_key)
        notif_center.close_drawer()
        screenshot(
            "TC-REQ-030-009_before-confirm",
            f"Notification centre before confirming reminder for '{plant_name}'",
        )

        pflege.open()
        pflege.click_confirm_on_card(plant_key, reminder_type)
        pflege.wait_for_confirm_dialog()
        pflege.submit_confirm_dialog()
        pflege.wait_for_dialog_closed()
        pflege.wait_for_loading_complete()

        notif_center.open_drawer()
        still_present = notif_center.has_notification(notif_key)
        now_unread = notif_center.is_unread(notif_key) if still_present else False
        screenshot(
            "TC-REQ-030-009_after-confirm",
            f"Notification centre after confirming reminder for '{plant_name}'",
        )

        assert was_unread and not now_unread, (
            "TC-REQ-030-009 FAIL (Soll): Expected confirming the reminder to auto-mark "
            f"the '{plant_name}'/{reminder_type} notification '{notif_key}' done "
            f"(was_unread={was_unread} -> now_unread={now_unread})"
        )


# -- TC-REQ-030-063 to 067: Source -> Notification Feedback (Soll) ------------


class TestNotificationSourcePropagation:
    """Source-change feedback into the notification centre (Soll: TC-REQ-030-063..067)."""

    @pytest.mark.requires_auth
    def test_moved_task_notification_shows_new_due(
        self,
        login_page: LoginPage,
        task_detail: TaskDetailPage,
        notif_center: NotificationCenterPage,
        base_url: str,
        e2e_seed_data: dict,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-063: Moving a task updates its notification's due date.

        Spec: TC-REQ-030-063 -- Quell-Aufgabe verschoben -- Benachrichtigung zeigt
        neue Faelligkeit (kein 'heute' mehr, kein Duplikat).
        """
        _ensure_logged_in(login_page)
        # Self-provisioned task due TODAY, so its fresh due-notification reads
        # 'heute' before the move (e2e-test-stability §A; asserts scoped to it).
        task_key, task_name = _create_e2e_task(e2e_seed_data, base_url, due_in_days=0)
        screenshot(
            "TC-REQ-030-010_before-move",
            f"Task {task_key} before moving its due date 4 days out",
        )

        target_due = (date.today() + timedelta(days=4)).isoformat()
        task_detail.open(task_key)
        task_detail.open_edit_tab()
        task_detail.set_due_date(target_due)
        task_detail.save_edit()

        texts = _drawer_notification_texts(notif_center)
        own = [t for t in texts if task_name in t]
        screenshot(
            "TC-REQ-030-010_after-move",
            "Notification centre after moving the task's due date",
        )

        assert own and not any(term in t.lower() for t in own for term in ("heute", "today")), (
            "TC-REQ-030-010 FAIL (Soll): Expected the task's own notification to show "
            f"the new due date (no stale 'heute') for '{task_name}', got: {own or texts}"
        )

    @pytest.mark.requires_auth
    def test_completed_task_notification_marked_done(
        self,
        login_page: LoginPage,
        task_queue: TaskQueuePage,
        notif_center: NotificationCenterPage,
        base_url: str,
        e2e_seed_data: dict,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-064: Completing a task marks its notification done.

        Spec: TC-REQ-030-064 -- Quell-Aufgabe abgeschlossen -- Benachrichtigung wird
        als erledigt/gelesen markiert.
        """
        _ensure_logged_in(login_page)
        # Self-provisioned task due today (e2e-test-stability §A); asserts are
        # scoped to its own notification instead of the global unread badge.
        task_key, task_name = _create_e2e_task(e2e_seed_data, base_url, due_in_days=0)

        notif_center.open_drawer()
        texts_before = _drawer_notification_texts(notif_center)
        if not any(task_name in t for t in texts_before):
            pytest.fail(
                "TC-REQ-030-011 precondition: expected a due-notification for "
                f"the fresh task '{task_name}', got: {texts_before}"
            )
        notif_center.close_drawer()
        screenshot(
            "TC-REQ-030-011_before-complete",
            f"Notification centre before completing task {task_key}",
        )

        task_queue.open()
        task_queue.complete_task(task_key)
        task_queue.wait_for_loading_complete()

        own_after = _poll_own_notifications_done(notif_center, task_name)
        screenshot(
            "TC-REQ-030-011_after-complete",
            "Notification centre after completing the task",
        )

        assert not own_after, (
            "TC-REQ-030-011 FAIL (Soll): Expected completing the source task to mark "
            f"its notification done/read; still unread: {own_after}"
        )

    @pytest.mark.requires_auth
    def test_deleted_source_removes_orphan_notification(
        self,
        login_page: LoginPage,
        task_detail: TaskDetailPage,
        notif_center: NotificationCenterPage,
        base_url: str,
        e2e_seed_data: dict,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-065: Deleting the source removes its orphaned notification.

        Spec: TC-REQ-030-065 -- Quell-Aufgabe/Erinnerung geloescht -- verwaiste
        Benachrichtigung wird entfernt bzw. als hinfaellig markiert.

        Self-provisioned own task (e2e-test-stability §A); the unread-badge
        assertion is dropped for the same reason as TC-REQ-030-006 -- it is
        the shared demo account's global count (§B), while the notification's
        item-scoped disappearance is a strictly stronger proof.
        """
        _ensure_logged_in(login_page)
        task_key, task_name = _create_e2e_task(e2e_seed_data, base_url)

        pre_texts = _drawer_notification_texts(notif_center)
        assert any(task_name in t for t in pre_texts), (
            f"Setup invariant: expected source task '{task_name}' to already have a "
            f"due-notification before deletion, got: {pre_texts}"
        )
        notif_center.close_drawer()
        screenshot(
            "TC-REQ-030-012_before-delete",
            f"Notification centre before deleting source task {task_key}",
        )

        task_detail.open(task_key)
        task_detail.delete_task()

        texts = _drawer_notification_texts(notif_center)
        screenshot(
            "TC-REQ-030-012_after-delete",
            "Notification centre after deleting source task",
        )

        assert not any(task_name in t for t in texts), (
            "TC-REQ-030-012 FAIL (Soll): Expected the orphaned notification for deleted "
            f"source '{task_name}' to be removed, got matches: "
            f"{[t for t in texts if task_name in t]}"
        )

    @pytest.mark.requires_auth
    def test_interval_change_yields_single_rescheduled_notification(
        self,
        login_page: LoginPage,
        pflege: PflegeDashboardPage,
        notif_center: NotificationCenterPage,
        base_url: str,
        e2e_seed_data: dict,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-066: Interval change reschedules the watering notification, no duplicate.

        Spec: TC-REQ-030-066 -- Giesszyklus angepasst -- care.watering-Benachrichtigung
        wird neu terminiert; genau ein Eintrag (group_key-Deduplizierung).

        Scoped to the edited plant's own notification (e2e-test-stability §B):
        the previous version counted watering-keyword matches across the
        entire drawer, so any *other* plant's watering reminder in the shared
        demo account (or a duplicate produced by a racing worker) inflated
        the count independently of this test's own action.
        """
        _ensure_logged_in(login_page)
        pflege.open()
        if pflege.get_care_card_count() == 0:
            pytest.skip("No care reminders available -- seed dependent")

        plant_key, reminder_type = _first_care_ids(pflege)
        # Resolve the plant's display name via the API: the notification body
        # carries the plant *name*, while the card's visible subtitle is the
        # care type (get_card_plant_name returned 'Umtopfen' here).
        from .conftest import _api_helpers, _fresh_access_token

        _, _get = _api_helpers(_fresh_access_token(e2e_seed_data, base_url))
        slug = e2e_seed_data.get("tenant_slug", "mein-garten")
        status, plant = _get(f"{base_url.rstrip('/')}/api/v1/t/{slug}/plant-instances/{plant_key}")
        plant_name = (
            (plant.get("name") or "").strip() if status == 200 and isinstance(plant, dict) else ""
        )
        if not plant_name:
            pytest.skip(f"Could not resolve plant name for key {plant_key} (status={status})")
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()
        if not pflege.is_present(PflegeDashboardPage.WATERING_INTERVAL_SLIDER):
            pytest.skip("Watering task not enabled on this profile -- no interval slider")
        pflege.set_watering_interval(14)
        pflege.click_save_profile()
        pflege.wait_for_loading_complete()

        texts = _drawer_notification_texts(notif_center)
        watering_texts = [
            t
            for t in texts
            if plant_name in t
            and any(term in t.lower() for term in ("gieß", "gie", "water", "wasser"))
        ]
        screenshot(
            "TC-REQ-030-013_after-interval-change",
            f"Notification centre after interval change for '{plant_name}' "
            f"({len(watering_texts)} watering notes)",
        )

        assert len(watering_texts) == 1, (
            "TC-REQ-030-013 FAIL (Soll): Expected exactly one rescheduled care.watering "
            f"notification for '{plant_name}' (no duplicate for the same period), got "
            f"{len(watering_texts)}: {watering_texts}"
        )

    @pytest.mark.requires_auth
    def test_actionable_done_button_confirms_source(
        self,
        login_page: LoginPage,
        pflege: PflegeDashboardPage,
        notif_center: NotificationCenterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-067: An actionable 'Erledigt' button confirms the source and marks done.

        Spec: TC-REQ-030-067 -- Actionable 'Erledigt'-Button schliesst die Quell-Aufgabe
        (CareConfirmation) und markiert die Benachrichtigung als erledigt.

        Seit Issue #742 rendert der NotificationDrawer pro actionable
        Care-/Task-Benachrichtigung einen dedizierten 'Erledigt'-Button
        (``notification-action-done-<key>``), der die Quelle in einem Schritt
        bestaetigt (CareConfirmation) und die Benachrichtigung als erledigt markiert.
        """
        _ensure_logged_in(login_page)
        pflege.open()
        if pflege.get_care_card_count() == 0:
            pytest.skip("No care reminders available -- seed dependent")

        notif_center.open_drawer()
        screenshot(
            "TC-REQ-030-014_notification-center",
            "Notification centre -- looking for an actionable 'Erledigt' button",
        )
        done_buttons = notif_center.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='notification-action-done-']"
        )

        assert done_buttons, (
            "TC-REQ-030-014 FAIL (Soll): Expected a dedicated actionable 'Erledigt' button "
            "per care.watering notification that confirms the source reminder in one step"
        )

        # Soll continuation: clicking it confirms the source and marks the note done.
        # Scoped to the actioned item itself (e2e-test-stability §B) instead of the
        # account-wide unread badge, which every parallel xdist worker mutates
        # concurrently (all full-mode tests share one demo user).
        button = done_buttons[0]
        notif_key = (button.get_attribute("data-testid") or "").replace(
            "notification-action-done-", ""
        )
        button.click()
        notif_center.wait_for_drawer()

        remaining_done_buttons = notif_center.driver.find_elements(
            By.CSS_SELECTOR, f"[data-testid='notification-action-done-{notif_key}']"
        )
        still_unread = (
            notif_center.is_unread(notif_key) if notif_center.has_notification(notif_key) else False
        )
        assert not remaining_done_buttons and not still_unread, (
            "TC-REQ-030-014 FAIL (Soll): Expected the actioned notification "
            f"'{notif_key}' to be marked done (acted_at set: Done button gone, "
            f"no longer unread), got done_button_present="
            f"{bool(remaining_done_buttons)}, unread={still_unread}"
        )
