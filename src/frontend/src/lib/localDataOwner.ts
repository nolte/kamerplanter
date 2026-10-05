/**
 * Which account may adopt this browser's anonymous leftovers (#2117, MT-020).
 *
 * Light mode, and the app before favorites and module visibility moved to the
 * server (#1233, REQ-042), kept them in `localStorage`. The carry-over thunks
 * move whatever they find into the profile of whoever is signed in — on a shared
 * device that was the *next* account, which then held the previous person's
 * favorites and module choices.
 *
 * The first account that adopts leftovers on this browser becomes their owner;
 * every other account leaves them where they are. Nothing is claimed while there
 * is nothing to adopt, so an account that never had leftovers does not lock out
 * the one that does.
 */

const OWNER_KEY = 'kp_local_data_owner';

/**
 * Whether *userKey* may move this browser's local leftovers into its profile.
 *
 * Call only when there is something to adopt. `false` without a signed-in
 * account (the profile may still be loading — the carry-over then waits for the
 * next start) and when storage is unavailable.
 */
export function mayAdoptLocalData(userKey: string | null | undefined): boolean {
  if (!userKey) return false;
  try {
    const owner = localStorage.getItem(OWNER_KEY);
    if (owner === null) {
      localStorage.setItem(OWNER_KEY, userKey);
      return true;
    }
    return owner === userKey;
  } catch {
    return false;
  }
}
