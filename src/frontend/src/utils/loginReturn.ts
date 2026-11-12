/**
 * The page a visitor without a session asked for, kept across the sign-in (UI-NFR-014 R-009…R-011).
 *
 * A protected page opened without a session redirects to `/login?returnTo=<path>` (R-009); a completed sign-in -
 * password or identity provider - continues there instead of the dashboard (R-010). This is what makes a bed label's
 * QR code (REQ-053 GP-UX-028) usable on a phone that is not signed in: scan, sign in, and the bed opens in field mode.
 *
 * The login page also remembers the path in `sessionStorage`, because a sign-in with an identity provider leaves the
 * app and comes back on `/auth/callback`, where the query of the login page is gone. A login page without `returnTo`
 * forgets it (a sign-out lands there), reaching a protected page signed in forgets it, and so does signing out.
 *
 * R-011 (open-redirect protection): only a same-origin, root-relative app path is ever used - `//host`, `/\host`, an
 * absolute URL, a scheme or a control character is dropped, and so are the sign-in pages themselves (no loop).
 */

const STORAGE_KEY = 'kamerplanter.loginReturnTo';

/** The query parameter of the login page that names the page to return to (UI-NFR-014 R-009). */
export const RETURN_TO_PARAM = 'returnTo';

/** Pages a sign-in never returns to: the sign-in itself and its neighbours, and the start page. */
const NO_RETURN_PREFIXES = [
  '/login',
  '/register',
  '/password-reset',
  '/verify-email',
  '/resend-verification',
  '/email-change',
  '/auth/',
  '/connect',
];

/** The invitation keeps its own memory (`pendingInvitation`, #2162); its accept page is not stored twice. */
const INVITATION_ACCEPT_PATH = '/invitations/accept';

function storage(): Storage | null {
  try {
    return window.sessionStorage;
  } catch {
    // Storage blocked (privacy mode, sandboxed frame): the return still works through the URL parameter.
    return null;
  }
}

function excluded(pathname: string): boolean {
  if (pathname === '/' || pathname === INVITATION_ACCEPT_PATH) return true;
  return NO_RETURN_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(prefix.endsWith('/') ? prefix : `${prefix}/`));
}

/**
 * *raw* as a same-origin app path (`/path?query#hash`) a sign-in may return to, or `null` (R-011).
 *
 * Root-relative only: the string must start with exactly one `/`. It is then resolved against the app's own origin,
 * so whatever a browser would read as another host (`//evil.example`, `/\evil.example`) fails the origin comparison.
 */
export function safeReturnTo(raw: string | null | undefined): string | null {
  if (!raw || !raw.startsWith('/') || raw.startsWith('//')) return null;
  // eslint-disable-next-line no-control-regex -- refusing control characters is the point of this check
  if (/[\u0000-\u001f\u007f\\]/.test(raw)) return null;
  let url: URL;
  try {
    url = new URL(raw, window.location.origin);
  } catch {
    return null;
  }
  if (url.origin !== window.location.origin || excluded(url.pathname)) return null;
  // Dot segments resolve during parsing (`/.//evil.example`, `/%2e%2e//evil.example` -> `//evil.example`): check the
  // path that is returned, not only the raw input, so the result is never protocol-relative.
  if (url.pathname.startsWith('//') || url.pathname.includes('\\')) return null;
  return `${url.pathname}${url.search}${url.hash}`;
}

/** The login page for a visitor sent away from *location*: `/login?returnTo=…`, or `/login` where nothing returns. */
export function loginPathFor(location: { pathname: string; search?: string; hash?: string }): string {
  const target = safeReturnTo(`${location.pathname}${location.search ?? ''}${location.hash ?? ''}`);
  return target ? `/login?${new URLSearchParams({ [RETURN_TO_PARAM]: target }).toString()}` : '/login';
}

/** Remember *path* (validated) for a sign-in that leaves the app (identity provider). */
export function rememberLoginReturn(path: string | null | undefined): void {
  const safe = safeReturnTo(path);
  if (safe) storage()?.setItem(STORAGE_KEY, safe);
}

/** The remembered return path, validated again on the way out; `null` when there is none. */
export function rememberedLoginReturn(): string | null {
  return safeReturnTo(storage()?.getItem(STORAGE_KEY));
}

/** Forget the remembered path - the visitor arrived, or signed out. */
export function forgetLoginReturn(): void {
  storage()?.removeItem(STORAGE_KEY);
}

/** The `returnTo` of a login page query (*search*), validated; `null` when it has none or an unsafe one. */
export function returnToFromSearch(search: string | null | undefined): string | null {
  if (!search) return null;
  return safeReturnTo(new URLSearchParams(search).get(RETURN_TO_PARAM));
}
