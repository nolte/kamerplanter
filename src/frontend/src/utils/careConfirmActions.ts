/**
 * Which notification action buttons *write* — and therefore need a rank (#1441).
 *
 * Tapping "Erledigt" on a `care.*` notification does not only stamp the row
 * read/acted: `POST …/notifications/{key}/act` confirms the source care reminder,
 * which persists a `CareConfirmation` and a `WateringLog`. Those are the writes
 * `require_permission('watering-log', CREATE)` refuses a viewer on the direct
 * route, so the backend refuses them here too — `mark_acted` in
 * `src/backend/app/api/v1/notifications/tenant_router.py` gates that one branch on
 * `MembershipEngine.can_edit_resource`.
 *
 * This module is the UI's mirror of that branch condition. It exists so a viewer
 * is not offered a button that can only answer 403; the *boundary* stays on the
 * server. The id list is the backend's `_CARE_CONFIRM_ACTIONS` set, and
 * `src/backend/tests/api/test_notification_act_role_gate.py` reads this file and
 * fails if the two drift apart.
 */
export const CARE_CONFIRM_ACTION_IDS = ['confirm', 'confirm_watering', 'done'] as const;

/** Prefix of the notification types whose confirm action reaches the care writes. */
export const CARE_NOTIFICATION_TYPE_PREFIX = 'care.';

/**
 * Whether tapping `actionId` on a notification of `notificationType` persists
 * care data — the exact branch condition the backend handler applies.
 */
export function isCareConfirmAction(
  notificationType: string,
  actionId: string,
): boolean {
  return (
    notificationType.startsWith(CARE_NOTIFICATION_TYPE_PREFIX) &&
    (CARE_CONFIRM_ACTION_IDS as readonly string[]).includes(actionId)
  );
}
