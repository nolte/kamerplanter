"""E2E tests for REQ-030 — Multi-Kanal-Benachrichtigungssystem.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-030.md):
  TC-REQ-030-001  ->  TC-030-009  Notification-Einstellungs-Tab in Kontoeinstellungen navigieren
  TC-REQ-030-002  ->  TC-030-010  Kanalverwaltung -- Uebersicht aller Kanaele
  TC-REQ-030-003  ->  TC-030-013  E-Mail-Kanal aktivieren und E-Mail-Adresse eintragen
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


# -- TC-REQ-030-001: Navigate to notification settings tab -------------------


class TestNotificationSettingsNavigation:
    """Notification settings tab navigation (Spec: TC-030-009)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_notification_tab_loads(
        self,
        login_page: LoginPage,
        notif_page: NotificationSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-001: Notification settings tab opens and renders the save button.

        Spec: TC-030-009 -- Notification-Einstellungs-Tab in Kontoeinstellungen
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
    """Channel toggle overview (Spec: TC-030-010)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_all_four_channels_rendered(
        self,
        login_page: LoginPage,
        notif_page: NotificationSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-002: All four delivery channels render with toggles.

        Spec: TC-030-010 -- Kanalverwaltung -- Uebersicht aller Kanaele.

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
    """Enable email channel and configure address (Spec: TC-030-013)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_enable_email_channel_and_save(
        self,
        login_page: LoginPage,
        notif_page: NotificationSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-003: Enable email channel, type address, save and verify.

        Spec: TC-030-013 -- E-Mail-Kanal aktivieren und E-Mail-Adresse
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
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        notif_center: NotificationCenterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-004: Reassigning a task delivers an assignment notification.

        Spec: TC-006-082 -- Aufgabe neu zuweisen -- 'Meine Aufgaben'-Filter und
        Benachrichtigung folgen der Zuweisung.

        Abweichung Spec vs. Impl: ein 'Meine Aufgaben'-Filter existiert im
        Frontend nicht; die Neuzuweisung via ``set_assigned_to`` ist setzbar und
        liefert dem neu zugewiesenen Mitglied eine Assignment-Benachrichtigung
        (Issue #742).
        """
        _ensure_logged_in(login_page)
        task_queue.open()
        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- seed dependent")
        key = keys[0]

        task_detail.open(key)
        task_name = task_detail.get_task_title()
        task_detail.open_edit_tab()
        task_detail.set_assigned_to("e2e-grower")
        task_detail.save_edit()
        screenshot(
            "TC-REQ-030-004_after-reassign",
            f"Task {key} reassigned to another member",
        )

        texts = _drawer_notification_texts(notif_center)
        screenshot(
            "TC-REQ-030-004_notification-center",
            "Notification centre after reassignment",
        )

        assert any("zugewiesen" in t.lower() or task_name in t for t in texts), (
            "TC-REQ-030-004 FAIL (Soll): Expected an assignment notification for the "
            f"reassigned task '{task_name}', got: {texts}"
        )

    @pytest.mark.requires_auth
    def test_edit_task_updates_existing_notification(
        self,
        login_page: LoginPage,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        notif_center: NotificationCenterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-005: Editing a task updates its existing due-notification in place.

        Spec: TC-006-083 -- Aufgabe bearbeiten -- zugehoerige Benachrichtigung
        wird synchron aktualisiert (kein Duplikat, kein veralteter Termin).
        """
        _ensure_logged_in(login_page)
        task_queue.open()
        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- seed dependent")
        key = keys[0]

        task_detail.open(key)
        original_name = task_detail.get_task_title()
        screenshot(
            "TC-REQ-030-005_before-edit",
            f"Notification centre / task {key} before edit",
        )

        new_name = f"{original_name} -- verschoben"
        target_due = (date.today() + timedelta(days=3)).isoformat()
        task_detail.open(key)
        task_detail.open_edit_tab()
        task_detail.set_name(new_name)
        task_detail.set_due_date(target_due)
        task_detail.save_edit()

        texts = _drawer_notification_texts(notif_center)
        screenshot(
            "TC-REQ-030-005_after-edit",
            "Notification centre after editing task name + due date",
        )

        assert any("verschoben" in t.lower() for t in texts), (
            "TC-REQ-030-005 FAIL (Soll): Expected the due-notification to reflect the "
            f"updated title '{new_name}', got: {texts}"
        )

    @pytest.mark.requires_auth
    def test_delete_task_removes_stale_notification(
        self,
        login_page: LoginPage,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        notif_center: NotificationCenterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-006: Deleting a task removes its stale due-notification.

        Spec: TC-006-084 -- Aufgabe loeschen -- veraltete Benachrichtigung wird
        entfernt und nicht mehr als ungelesen gezaehlt.
        """
        _ensure_logged_in(login_page)
        task_queue.open()
        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- seed dependent")
        key = keys[0]

        task_detail.open(key)
        task_name = task_detail.get_task_title()

        notif_center.open_drawer()
        initial_badge = notif_center.get_unread_badge_count()
        notif_center.close_drawer()
        screenshot(
            "TC-REQ-030-006_before-delete",
            f"Notification centre before deleting task {key} (badge={initial_badge})",
        )

        task_detail.open(key)
        task_detail.delete_task()

        texts = _drawer_notification_texts(notif_center)
        new_badge = notif_center.get_unread_badge_count()
        screenshot(
            "TC-REQ-030-006_after-delete",
            f"Notification centre after deleting task (badge={new_badge})",
        )

        assert not any(task_name in t for t in texts) and new_badge < initial_badge, (
            "TC-REQ-030-006 FAIL (Soll): Expected the stale notification for the deleted "
            f"task '{task_name}' to be removed and the unread badge to decrement "
            f"({initial_badge} -> {new_badge}), got: {texts}"
        )

    @pytest.mark.requires_auth
    def test_complete_task_marks_notification_done(
        self,
        login_page: LoginPage,
        task_queue: TaskQueuePage,
        notif_center: NotificationCenterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-007: Completing a task auto-marks its due-notification done.

        Spec: TC-006-085 -- Aufgabe abschliessen -- offene Faellig-Benachrichtigung
        wird als erledigt markiert (nicht mehr im ungelesen-Badge).
        """
        _ensure_logged_in(login_page)
        task_queue.open()
        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- seed dependent")
        key = keys[0]

        notif_center.open_drawer()
        initial_badge = notif_center.get_unread_badge_count()
        notif_center.close_drawer()
        screenshot(
            "TC-REQ-030-007_before-complete",
            f"Notification centre before completing task {key} (badge={initial_badge})",
        )

        task_queue.open()
        task_queue.complete_task(key)
        task_queue.wait_for_loading_complete()

        notif_center.open_drawer()
        new_badge = notif_center.get_unread_badge_count()
        screenshot(
            "TC-REQ-030-007_after-complete",
            f"Notification centre after completing task (badge={new_badge})",
        )

        assert new_badge < initial_badge, (
            "TC-REQ-030-007 FAIL (Soll): Expected completing the task to auto-mark its "
            f"due-notification read (unread badge {initial_badge} -> should decrease), "
            f"got {new_badge}"
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
        """TC-REQ-030-008: Lengthening the watering interval reschedules the notification.

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
            any(term in t.lower() for term in ("gieß", "gie", "water", "wasser"))
            for t in texts
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
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-009: Confirming a reminder auto-marks its notification done.

        Spec: TC-022-094 -- Erinnerung bestaetigen -- zugehoerige Benachrichtigung
        wird als erledigt markiert (nicht mehr im ungelesen-Badge).
        """
        _ensure_logged_in(login_page)
        pflege.open()
        plant_key, reminder_type = _first_care_ids(pflege)

        notif_center.open_drawer()
        initial_badge = notif_center.get_unread_badge_count()
        notif_center.close_drawer()
        screenshot(
            "TC-REQ-030-009_before-confirm",
            f"Notification centre before confirming reminder (badge={initial_badge})",
        )

        pflege.open()
        pflege.click_confirm_on_card(plant_key, reminder_type)
        pflege.wait_for_confirm_dialog()
        pflege.submit_confirm_dialog()
        pflege.wait_for_dialog_closed()
        pflege.wait_for_loading_complete()

        notif_center.open_drawer()
        new_badge = notif_center.get_unread_badge_count()
        screenshot(
            "TC-REQ-030-009_after-confirm",
            f"Notification centre after confirming reminder (badge={new_badge})",
        )

        assert new_badge < initial_badge, (
            "TC-REQ-030-009 FAIL (Soll): Expected confirming the reminder to auto-mark "
            f"its notification read (unread badge {initial_badge} -> should decrease), "
            f"got {new_badge}"
        )


# -- TC-REQ-030-063 to 067: Source -> Notification Feedback (Soll) ------------


class TestNotificationSourcePropagation:
    """Source-change feedback into the notification centre (Soll: TC-REQ-030-063..067)."""

    @pytest.mark.requires_auth
    def test_moved_task_notification_shows_new_due(
        self,
        login_page: LoginPage,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        notif_center: NotificationCenterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-010: Moving a task updates its notification's due date.

        Spec: TC-REQ-030-063 -- Quell-Aufgabe verschoben -- Benachrichtigung zeigt
        neue Faelligkeit (kein 'heute' mehr, kein Duplikat).
        """
        _ensure_logged_in(login_page)
        task_queue.open()
        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- seed dependent")
        key = keys[0]

        task_detail.open(key)
        task_name = task_detail.get_task_title()
        screenshot(
            "TC-REQ-030-010_before-move",
            f"Task {key} before moving its due date 4 days out",
        )

        target_due = (date.today() + timedelta(days=4)).isoformat()
        task_detail.open(key)
        task_detail.open_edit_tab()
        task_detail.set_due_date(target_due)
        task_detail.save_edit()

        texts = _drawer_notification_texts(notif_center)
        screenshot(
            "TC-REQ-030-010_after-move",
            "Notification centre after moving the task's due date",
        )

        assert any(task_name in t for t in texts) and not any(
            term in t.lower() for t in texts for term in ("heute", "today")
        ), (
            "TC-REQ-030-010 FAIL (Soll): Expected the task notification to show the new "
            f"due date (no stale 'heute') for '{task_name}', got: {texts}"
        )

    @pytest.mark.requires_auth
    def test_completed_task_notification_marked_done(
        self,
        login_page: LoginPage,
        task_queue: TaskQueuePage,
        notif_center: NotificationCenterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-011: Completing a task marks its notification done.

        Spec: TC-REQ-030-064 -- Quell-Aufgabe abgeschlossen -- Benachrichtigung wird
        als erledigt/gelesen markiert.
        """
        _ensure_logged_in(login_page)
        task_queue.open()
        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- seed dependent")
        key = keys[0]

        notif_center.open_drawer()
        initial_badge = notif_center.get_unread_badge_count()
        notif_center.close_drawer()
        screenshot(
            "TC-REQ-030-011_before-complete",
            f"Notification centre before completing task {key} (badge={initial_badge})",
        )

        task_queue.open()
        task_queue.complete_task(key)
        task_queue.wait_for_loading_complete()

        notif_center.open_drawer()
        new_badge = notif_center.get_unread_badge_count()
        screenshot(
            "TC-REQ-030-011_after-complete",
            f"Notification centre after completing task (badge={new_badge})",
        )

        assert new_badge < initial_badge, (
            "TC-REQ-030-011 FAIL (Soll): Expected completing the source task to mark its "
            f"notification read (unread badge {initial_badge} -> should decrease), "
            f"got {new_badge}"
        )

    @pytest.mark.requires_auth
    def test_deleted_source_removes_orphan_notification(
        self,
        login_page: LoginPage,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        notif_center: NotificationCenterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-012: Deleting the source removes its orphaned notification.

        Spec: TC-REQ-030-065 -- Quell-Aufgabe/Erinnerung geloescht -- verwaiste
        Benachrichtigung wird entfernt bzw. als hinfaellig markiert.
        """
        _ensure_logged_in(login_page)
        task_queue.open()
        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- seed dependent")
        key = keys[0]

        task_detail.open(key)
        task_name = task_detail.get_task_title()

        notif_center.open_drawer()
        initial_badge = notif_center.get_unread_badge_count()
        notif_center.close_drawer()
        screenshot(
            "TC-REQ-030-012_before-delete",
            f"Notification centre before deleting source task {key} (badge={initial_badge})",
        )

        task_detail.open(key)
        task_detail.delete_task()

        texts = _drawer_notification_texts(notif_center)
        new_badge = notif_center.get_unread_badge_count()
        screenshot(
            "TC-REQ-030-012_after-delete",
            f"Notification centre after deleting source task (badge={new_badge})",
        )

        assert not any(task_name in t for t in texts) and new_badge < initial_badge, (
            "TC-REQ-030-012 FAIL (Soll): Expected the orphaned notification for deleted "
            f"source '{task_name}' to be removed and the unread badge to decrement "
            f"({initial_badge} -> {new_badge}), got: {texts}"
        )

    @pytest.mark.requires_auth
    def test_interval_change_yields_single_rescheduled_notification(
        self,
        login_page: LoginPage,
        pflege: PflegeDashboardPage,
        notif_center: NotificationCenterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-013: Interval change reschedules the watering notification, no duplicate.

        Spec: TC-REQ-030-066 -- Giesszyklus angepasst -- care.watering-Benachrichtigung
        wird neu terminiert; genau ein Eintrag (group_key-Deduplizierung).
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
        pflege.set_watering_interval(14)
        pflege.click_save_profile()
        pflege.wait_for_loading_complete()

        texts = _drawer_notification_texts(notif_center)
        watering_texts = [
            t
            for t in texts
            if any(term in t.lower() for term in ("gieß", "gie", "water", "wasser"))
        ]
        screenshot(
            "TC-REQ-030-013_after-interval-change",
            f"Notification centre after interval change ({len(watering_texts)} watering notes)",
        )

        assert len(watering_texts) == 1, (
            "TC-REQ-030-013 FAIL (Soll): Expected exactly one rescheduled care.watering "
            f"notification (no duplicate for the same period), got {len(watering_texts)}: "
            f"{watering_texts}"
        )

    @pytest.mark.requires_auth
    def test_actionable_done_button_confirms_source(
        self,
        login_page: LoginPage,
        pflege: PflegeDashboardPage,
        notif_center: NotificationCenterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-014: An actionable 'Erledigt' button confirms the source and marks done.

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
        done_buttons[0].click()
        notif_center.wait_for_drawer()
        new_badge = notif_center.get_unread_badge_count()
        assert new_badge == 0, (
            "TC-REQ-030-014 FAIL (Soll): Expected the actioned notification to be marked "
            f"done (acted_at set, unread badge -> 0), got {new_badge}"
        )
