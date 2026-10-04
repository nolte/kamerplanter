import type { OidcProvider, OidcProviderUpdate } from '@/api/types';

/**
 * The fields whose change needs no step-up: they change how a provider is shown, not whom a
 * sign-in resolves to. Mirrors `_PRESENTATION_FIELDS` in `oidc_provider_admin_service.py`
 * (operator decision D6) — an allow-list, so a field added later defaults to needing one.
 * Switching a provider on *or off* is deliberately not in it.
 */
const PRESENTATION_FIELDS: ReadonlySet<string> = new Set(['display_name', 'icon_url']);

/**
 * Whether applying `payload` to `current` changes anything a sign-in depends on, i.e. whether
 * the backend will ask for the admin's step-up (`update_requires_step_up`).
 *
 * A field sent with the value it already has is no change; a client secret is always one (its
 * stored value is encrypted and cannot be compared). The backend stays the authority: this
 * only decides whether the page opens the confirmation dialog first instead of letting the
 * request answer 401.
 */
export function oidcUpdateNeedsStepUp(current: OidcProvider, payload: OidcProviderUpdate): boolean {
  for (const [field, value] of Object.entries(payload)) {
    if (value === undefined) continue;
    if (field === 'client_secret') return true;
    if (PRESENTATION_FIELDS.has(field)) continue;
    if ((current as unknown as Record<string, unknown>)[field] === value) continue;
    // Scopes are a list: equal content is no change.
    if (field === 'scopes' && sameList(current.scopes, value as string[])) continue;
    return true;
  }
  return false;
}

function sameList(a: readonly string[], b: readonly string[]): boolean {
  return a.length === b.length && a.every((v, i) => v === b[i]);
}

/** `"openid email, profile"` → `['openid','email','profile']`; empty entries dropped, order kept. */
export function parseScopes(text: string): string[] {
  return text
    .split(/[\s,]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

/**
 * GitHub only exposes whether an address is verified through `GET /user/emails`, which needs
 * `user:email` (or the parent `user`); the API refuses a GitHub provider without one with 422
 * (#1477). Checked here too so the form says so before the admin spends a step-up on it.
 * Several scopes may share one entry (`"read:user user:email"`), as on the backend.
 */
export function githubScopesLackEmail(scopes: readonly string[]): boolean {
  const tokens = scopes.flatMap((s) => s.split(/\s+/)).filter(Boolean);
  return !tokens.includes('user:email') && !tokens.includes('user');
}
