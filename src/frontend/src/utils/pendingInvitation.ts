/**
 * The invitation an unauthenticated visitor opened, kept across the sign-in (#2162).
 *
 * `/invitations/accept?token=…` is a protected route: a visitor who is not signed in is sent to
 * `/login`, and the token in the URL used to be lost on the way — whoever followed an invitation
 * mail without a session landed on the dashboard and never joined. `ProtectedRoute` now remembers
 * the token here before it redirects; the sign-in (password or identity provider) then continues
 * at {@link postLoginPath} instead of the dashboard, and the accept page forgets the token once it
 * has it.
 *
 * `sessionStorage`, not `localStorage`: the token stays in the tab that opened the link and ends
 * with it. It is no more exposed than the URL it came from, and accepting still needs the invited,
 * proven address (REQ-024 AK-61) or, for a link invitation, a signed-in account.
 */

import { rememberedLoginReturn, returnToFromSearch } from './loginReturn';

const STORAGE_KEY = 'kamerplanter.pendingInvitation';
const ACCEPT_PATH = '/invitations/accept';

function storage(): Storage | null {
  try {
    return window.sessionStorage;
  } catch {
    // Storage blocked (privacy mode, sandboxed frame): the invitation link has to be opened again.
    return null;
  }
}

/** Remember *token* when an unauthenticated visitor is sent away from the accept page. */
export function rememberPendingInvitation(token: string): void {
  if (token) storage()?.setItem(STORAGE_KEY, token);
}

/** The remembered invitation token, or `null`. */
export function pendingInvitationToken(): string | null {
  return storage()?.getItem(STORAGE_KEY) || null;
}

/** Forget the remembered token — the accept page has it, or it was used. */
export function forgetPendingInvitation(): void {
  storage()?.removeItem(STORAGE_KEY);
}

/** The accept page for *token*. */
export function invitationAcceptPath(token: string): string {
  return `${ACCEPT_PATH}?token=${encodeURIComponent(token)}`;
}

/**
 * Where a completed sign-in continues: the remembered invitation, else the page the visitor was sent
 * away from (UI-NFR-014 R-010: the login page's `returnTo` in *search*, else the remembered one -
 * see `loginReturn`), else the dashboard.
 *
 * Reads without consuming: the login page and the public-only route guard both ask after the same
 * sign-in, and both must get the same answer. The accept page forgets the token; reaching a
 * protected page signed in forgets the return path.
 */
export function postLoginPath(search?: string): string {
  const token = pendingInvitationToken();
  if (token) return invitationAcceptPath(token);
  return returnToFromSearch(search) ?? rememberedLoginReturn() ?? '/dashboard';
}

/** Whether *pathname* is the accept page. */
export function isInvitationAcceptPath(pathname: string): boolean {
  return pathname === ACCEPT_PATH;
}
