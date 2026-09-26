import type { AuthProviderInfo, StepUpAction } from '@/api/types';

/**
 * Browser-side state of the fresh sign-in that confirms a step-up (#1815).
 *
 * The flow leaves the app: the dialog asks the backend for the provider's
 * authorization URL and sends the browser there; the provider comes back via the
 * backend to `/auth/step-up/callback` with a one-time token in the URL fragment.
 * Three small records bridge that round trip, all in **sessionStorage** — never
 * localStorage (the token must not outlive the tab), never logged:
 *
 * - the **pending token** (`{token, action, target, expiresAt}`), written by the
 *   callback page and consumed by the step-up that sends it — only by one for
 *   the same act *and target* (#1884);
 * - the **resume context** (`{surface, action, target, returnPath}`), written just
 *   before the redirect so the page can reopen the dialog it came from;
 * - the **error marker** (`{error, action, expiresAt}`), written by the callback
 *   page on `?error=…` so the reopened dialog can say why.
 */

/** The one sessionStorage key of the pending step-up token. */
export const STEP_UP_REAUTH_TOKEN_KEY = 'kp.stepUp.token';
/** Where the browser returns to, and which surface reopens, after the provider. */
export const STEP_UP_REAUTH_RESUME_KEY = 'kp.stepUp.resume';
/** The (whitelisted) error code of a failed fresh sign-in. */
export const STEP_UP_REAUTH_ERROR_KEY = 'kp.stepUp.error';

/** Lifetime of the backend's step-up token: five minutes, single use. */
export const STEP_UP_TOKEN_TTL_MS = 5 * 60 * 1000;
/** How long a started fresh sign-in may take before its callback is no longer accepted. */
export const STEP_UP_RESUME_TTL_MS = 10 * 60 * 1000;

/**
 * One entry per act — a `Record` over the union, so an act added to
 * `StepUpAction` without being listed here fails the type check instead of
 * silently making its fresh-sign-in callback unacceptable (#1847).
 */
const STEP_UP_ACTION_SET: Readonly<Record<StepUpAction, true>> = {
  account_erasure: true,
  admin_account_erasure: true,
  tenant_deletion: true,
  password_change: true,
  email_change: true,
  api_key_creation: true,
  device_pairing: true,
  provider_unlink: true,
  admin_account_update: true,
  oidc_provider_change: true,
};

/**
 * Whether an act acts on something other than the own account (#1884) — its code
 * and token are then bound to that target. A `Record` over the union, like the
 * set above, so a new act must be classified. Mirrors `TARGETED_ACTIONS` in
 * `step_up_service.py`.
 */
const TARGETED_STEP_UP_ACTIONS: Readonly<Record<StepUpAction, boolean>> = {
  account_erasure: false,
  admin_account_erasure: true,
  tenant_deletion: true,
  password_change: false,
  email_change: false,
  api_key_creation: false,
  device_pairing: false,
  provider_unlink: true,
  admin_account_update: true,
  oidc_provider_change: true,
};

export function isTargetedStepUpAction(action: StepUpAction): boolean {
  return TARGETED_STEP_UP_ACTIONS[action];
}

/** The stored spelling of "no target": `null`, whether the caller passed `undefined` or `null`. */
function normalizeTarget(target: string | null | undefined): string | null {
  return typeof target === 'string' && target.length > 0 ? target : null;
}

/** Every act a step-up confirms — mirrors `StepUpAction` in `step_up_service.py`. */
export const STEP_UP_ACTIONS: readonly StepUpAction[] = Object.keys(STEP_UP_ACTION_SET) as StepUpAction[];

/** Provider types that cannot prove a fresh sign-in (GitHub: plain OAuth2; Apple: no `auth_time`). */
const NO_FRESH_REAUTH_PROVIDERS: ReadonlySet<string> = new Set(['local', 'github', 'apple']);

export function isStepUpAction(value: unknown): value is StepUpAction {
  return typeof value === 'string' && (STEP_UP_ACTIONS as readonly string[]).includes(value);
}

/**
 * The linked providers that can confirm a step-up with a fresh sign-in.
 *
 * Everything but `local`, `github` and `apple` — a provider type the frontend
 * does not know yet is offered too; the backend answers 422 if it cannot, and
 * the surface falls back to the e-mailed code.
 */
export function reauthCapableProviders(
  providers: readonly AuthProviderInfo[] | null | undefined,
): AuthProviderInfo[] {
  return (providers ?? []).filter((p) => !NO_FRESH_REAUTH_PROVIDERS.has(p.provider));
}

/**
 * Whether `path` is a same-origin, app-relative path — the open-redirect guard
 * for the return path read back from sessionStorage.
 *
 * It must start with a single `/`; `//host` and `/\host` (which browsers
 * normalise to `//host`) are protocol-relative URLs to another origin. Control
 * characters and backslashes are refused outright, and the resolved URL must
 * keep the app's origin.
 */
export function isSafeReturnPath(path: unknown): path is string {
  if (typeof path !== 'string' || path.length === 0 || path.length > 2048) return false;
  if (!path.startsWith('/') || path.startsWith('//')) return false;
  // eslint-disable-next-line no-control-regex
  if (/[\u0000-\u001f\u007f\\]/.test(path)) return false;
  try {
    return new URL(path, window.location.origin).origin === window.location.origin;
  } catch {
    return false;
  }
}

function readJson(key: string): Record<string, unknown> | null {
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

function writeJson(key: string, value: object): void {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Storage unavailable (private mode, quota): the flow degrades to a plain retry.
  }
}

function remove(key: string): void {
  try {
    sessionStorage.removeItem(key);
  } catch {
    // Nothing stored that could be removed.
  }
}

// ── Pending token ───────────────────────────────────────────────────

/** Keep the token of a fresh sign-in for `action` on `target`, valid for five minutes from `now`. */
export function storePendingStepUpToken(
  token: string,
  action: StepUpAction,
  target: string | null | undefined,
  now: number = Date.now(),
): void {
  writeJson(STEP_UP_REAUTH_TOKEN_KEY, {
    token,
    action,
    target: normalizeTarget(target),
    expiresAt: now + STEP_UP_TOKEN_TTL_MS,
  });
}

/**
 * The pending token for `action` on `target`, or `null` — none, another act's or
 * another target's (#1884: the backend refuses it there anyway), or expired. An
 * expired or malformed record is dropped on the way.
 */
export function peekPendingStepUpToken(
  action: StepUpAction,
  target: string | null | undefined,
  now: number = Date.now(),
): string | null {
  const record = readJson(STEP_UP_REAUTH_TOKEN_KEY);
  if (!record) {
    remove(STEP_UP_REAUTH_TOKEN_KEY);
    return null;
  }
  const { token, action: recordAction, target: recordTarget, expiresAt } = record;
  if (
    typeof token !== 'string' ||
    token.length === 0 ||
    typeof expiresAt !== 'number' ||
    expiresAt <= now
  ) {
    remove(STEP_UP_REAUTH_TOKEN_KEY);
    return null;
  }
  const sameTarget = normalizeTarget(recordTarget as string | null) === normalizeTarget(target);
  return recordAction === action && sameTarget ? token : null;
}

/** Take the pending token for `action` on `target` out of storage — it is single use. */
export function consumePendingStepUpToken(
  action: StepUpAction,
  target: string | null | undefined,
  now: number = Date.now(),
): string | null {
  const token = peekPendingStepUpToken(action, target, now);
  if (token !== null) remove(STEP_UP_REAUTH_TOKEN_KEY);
  return token;
}

// ── Error marker ────────────────────────────────────────────────────

/** Leave the callback's (whitelisted) error code for the step-up of `action`. */
export function storeStepUpReauthError(
  error: string,
  action: StepUpAction,
  now: number = Date.now(),
): void {
  writeJson(STEP_UP_REAUTH_ERROR_KEY, { error, action, expiresAt: now + STEP_UP_TOKEN_TTL_MS });
}

/** The error marker for `action`, without removing it. */
export function peekStepUpReauthError(
  action: StepUpAction,
  now: number = Date.now(),
): string | null {
  const record = readJson(STEP_UP_REAUTH_ERROR_KEY);
  if (!record) {
    remove(STEP_UP_REAUTH_ERROR_KEY);
    return null;
  }
  const { error, action: recordAction, expiresAt } = record;
  if (typeof error !== 'string' || typeof expiresAt !== 'number' || expiresAt <= now) {
    remove(STEP_UP_REAUTH_ERROR_KEY);
    return null;
  }
  return recordAction === action ? error : null;
}

/** The error marker for `action`, removed — it is shown once. */
export function takeStepUpReauthError(
  action: StepUpAction,
  now: number = Date.now(),
): string | null {
  const error = peekStepUpReauthError(action, now);
  if (error !== null) remove(STEP_UP_REAUTH_ERROR_KEY);
  return error;
}

// ── Resume context ──────────────────────────────────────────────────

/** Which surface started the fresh sign-in, for which act, and where to return. */
export interface StepUpResumeInput {
  /** The step-up surface's id — the dialog's `testIdPrefix`, e.g. `delete-account`. */
  surface: string;
  action: StepUpAction;
  /** What the act acts on (#1884) — the key the token is bound to; absent for an act on the own account. */
  target?: string | null;
  /** App-relative path including search and hash, e.g. `/admin/tenants/abc` or `/account#security`. */
  returnPath: string;
}

/**
 * The saved resume record. `nonce` (random, per start) is sent to the backend as
 * `client_nonce` and comes back beside the token or error; the callback keeps a
 * result only when it carries this nonce, a record for the same act exists and
 * it is younger than {@link STEP_UP_RESUME_TTL_MS} (SEC-005) — a link someone
 * else crafted neither lands in a tab with such a record nor knows the nonce.
 */
export interface StepUpResume extends StepUpResumeInput {
  target: string | null;
  nonce: string;
  createdAt: number;
}

/** A fresh client nonce for one re-authentication: 32 lowercase hex characters. */
export function newStepUpClientNonce(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Remember where to come back to before the browser leaves for the provider.
 * Returns the nonce kept with the record — pass the one sent as `client_nonce`.
 */
export function saveStepUpResume(
  resume: StepUpResumeInput & { nonce?: string },
  now: number = Date.now(),
): string {
  const nonce = resume.nonce ?? newStepUpClientNonce();
  writeJson(STEP_UP_REAUTH_RESUME_KEY, {
    surface: resume.surface,
    action: resume.action,
    target: normalizeTarget(resume.target),
    returnPath: resume.returnPath,
    nonce,
    createdAt: now,
  });
  return nonce;
}

/**
 * The saved resume context, or `null` when there is none, it fails validation
 * (unsafe return path, unknown act, no nonce) or it is older than
 * {@link STEP_UP_RESUME_TTL_MS}.
 */
export function readStepUpResume(now: number = Date.now()): StepUpResume | null {
  const record = readJson(STEP_UP_REAUTH_RESUME_KEY);
  if (!record) return null;
  const { surface, action, target, returnPath, nonce, createdAt } = record;
  if (typeof surface !== 'string' || !isStepUpAction(action) || !isSafeReturnPath(returnPath))
    return null;
  if (target !== undefined && target !== null && typeof target !== 'string') return null;
  if (typeof nonce !== 'string' || nonce.length === 0) return null;
  if (typeof createdAt !== 'number' || createdAt > now || now - createdAt > STEP_UP_RESUME_TTL_MS)
    return null;
  return { surface, action, target: normalizeTarget(target), returnPath, nonce, createdAt };
}

export function clearStepUpResume(): void {
  remove(STEP_UP_REAUTH_RESUME_KEY);
}

/** The pathname of an app-relative return path (search and hash dropped). */
export function returnPathname(returnPath: string): string {
  try {
    return new URL(returnPath, window.location.origin).pathname;
  } catch {
    return returnPath;
  }
}
