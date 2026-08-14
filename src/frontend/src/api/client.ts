import axios, { AxiosHeaders, type InternalAxiosRequestConfig } from 'axios';
import { ApiError } from './errors';
import type { ApiErrorResponse } from './types';
import { isLightMode } from '@/config/mode';

const LIGHT_MODE_SLUG = 'mein-garten';

/**
 * Request header naming the tenant the caller is acting in on a **global**
 * (path-less) route — the species, cultivar, botanical-family and
 * companion-planting catalogues (ADR-009, REQ-049 §2.11, #1091).
 *
 * Those routes carry no `/t/{slug}/` segment to bind a tenant to, so without
 * this header the backend falls back to the caller's *personal* tenant: a user
 * acting in an organisation would read and create catalogue rows in their own
 * garden instead. The value is the tenant **slug** — the same identifier
 * `/t/{slug}/` and `kp_active_tenant_slug` already use.
 *
 * Mirrors the backend's single source `ACTIVE_TENANT_HEADER`
 * (`src/backend/app/common/auth.py`); the two spellings must stay identical.
 */
export const ACTIVE_TENANT_HEADER = 'X-Active-Tenant';

/**
 * The backend's one refusal message for a caller-supplied tenant slug it will
 * not honour — an unknown slug and a tenant the caller holds no active
 * membership in are answered identically, on purpose (no tenant-existence
 * oracle). Mirrors `_ACTIVE_TENANT_DENIED` in `app/common/auth.py`.
 *
 * Used here as the *discriminator* for stale-slug recovery — see
 * {@link isStaleActiveTenantRejection} for why the message, and not the status
 * code or the error code, is what tells this refusal apart from an ordinary
 * role refusal.
 */
export const ACTIVE_TENANT_DENIED_MESSAGE = 'You do not have access to the requested tenant.';

/**
 * Active tenant slug, kept in sync by tenantSlice.
 * This avoids reading a stale value from localStorage before
 * loadMyTenants has validated the persisted slug.
 */
let _activeTenantSlug: string | null = null;

export function setActiveTenantSlug(slug: string | null) {
  _activeTenantSlug = slug;
}

export function getActiveTenantSlug(): string | null {
  return _activeTenantSlug;
}

/**
 * Resolve once the active tenant slug is known (or the timeout elapses).
 *
 * During auth bootstrap the slug is still null while ``loadMyTenants`` is in
 * flight; firing a tenant-scoped request in that window used to hit the
 * unprefixed path (``/api/v1/user-preferences`` instead of
 * ``/api/v1/t/{slug}/user-preferences``) and 404 — thousands of doomed
 * requests per session and sporadic error banners on freshly loaded pages.
 */
function waitForTenantSlug(timeoutMs = 10000): Promise<string | null> {
  if (_activeTenantSlug) return Promise.resolve(_activeTenantSlug);
  return new Promise((resolve) => {
    const started = Date.now();
    const timer = setInterval(() => {
      if (_activeTenantSlug || Date.now() - started > timeoutMs) {
        clearInterval(timer);
        resolve(_activeTenantSlug);
      }
    }, 50);
  });
}

/**
 * Shared response-interceptor rejection handler: converts a backend error
 * envelope ({ error_id, error_code, ... }) into a typed {@link ApiError} and
 * re-throws everything else unchanged. Used by both `client` and `tenantClient`
 * so the envelope-detection logic lives in exactly one place.
 */
function rethrowApiError(error: unknown): never {
  if (axios.isAxiosError(error) && error.response) {
    const data = error.response.data as ApiErrorResponse;
    if (data?.error_id && data?.error_code) {
      throw new ApiError(data, error.response.status);
    }
  }
  throw error;
}

/** Recovery callback invoked when the backend refuses the active tenant slug. */
export type ActiveTenantRejectedHandler = () => void | Promise<unknown>;

let _activeTenantRejectedHandler: ActiveTenantRejectedHandler | null = null;
let _activeTenantRecoveryInFlight = false;

/**
 * Register what should happen when the backend refuses the active tenant slug.
 *
 * Inversion of control on purpose: this module must not import the Redux store
 * (every slice imports *this* module, so the reverse edge would be a cycle),
 * yet recovery has to reach state that only the store owns — the tenant list and
 * the `activeTenant` the switcher renders. The composition root
 * (`store/store.ts`) therefore hands the behaviour in. Passing `null` unregisters.
 */
export function setActiveTenantRejectedHandler(handler: ActiveTenantRejectedHandler | null) {
  _activeTenantRejectedHandler = handler;
}

/**
 * Whether the failed request actually carried {@link ACTIVE_TENANT_HEADER}.
 *
 * Routed through `AxiosHeaders.from` rather than a property lookup: it accepts
 * both shapes `config.headers` can have (the normalised `AxiosHeaders` of a
 * dispatched request and a plain object handed in by a caller) and it matches
 * the name case-insensitively, which is what HTTP guarantees and a bracket
 * lookup does not.
 */
function requestCarriedActiveTenantHeader(config?: InternalAxiosRequestConfig): boolean {
  const headers = config?.headers;
  if (!headers) return false;
  return Boolean(AxiosHeaders.from(headers).get(ACTIVE_TENANT_HEADER));
}

/**
 * Does this rejection say "the tenant you claimed to act in is not yours"?
 *
 * The discrimination problem, and why it is solved by the *message*: a stale
 * slug and an under-privileged role produce the **same** status (403) and the
 * **same** `error_code` (`FORBIDDEN`), yet demand opposite reactions. A stale
 * slug must clear the active tenant — it locks the caller out of *all* ~19
 * catalogue operations at once, so leaving it in place is a permanent dead end.
 * A role refusal (an org viewer pressing "create species", the SEC-005/#1113
 * gate) must change nothing: the caller is a legitimate member acting in the
 * right tenant, and silently dropping them back to their personal garden would
 * turn a "you may not do this" into a confusing context switch.
 *
 * Three conditions must hold together, and each one is load-bearing:
 *
 * 1. the request carried the header — a refusal of a request that never claimed
 *    a tenant cannot be about the claimed tenant;
 * 2. status 403 with `error_code` `FORBIDDEN`;
 * 3. the body carries exactly {@link ACTIVE_TENANT_DENIED_MESSAGE}.
 *
 * Rejected alternatives:
 *
 * * *"recover on every 403 that carried the header"* — fires on the role gate
 *   above and on `require_platform_admin` GETs in the admin panel, both of which
 *   would nuke a perfectly valid active tenant.
 * * *"recover only on GET/list requests"* — still catches admin-panel GETs, and
 *   misses the real case of a stale slug breaking a catalogue **create**.
 * * *"retry the request without the header and see if it succeeds"* — precise
 *   but it would re-send a `POST`, creating the row in the personal tenant.
 *
 * Matching a message is admittedly a soft contract, so the failure direction was
 * chosen deliberately: if the backend ever rewords `_ACTIVE_TENANT_DENIED`, this
 * predicate goes *false* and recovery simply stops happening — the pre-#1091
 * status quo, where the user re-picks a tenant in the switcher. The opposite
 * mistake (a broad match that fires on role refusals) would be silent and
 * user-visible. A machine-readable marker in the envelope's `details` would be
 * strictly better and is the recommended backend follow-up.
 */
/**
 * Whether a failure is a rate limit rather than a rejected credential (#1131).
 *
 * `/auth/refresh` carries a per-IP budget, and the 401 interceptor reaches it on
 * every expired access token — behind a shared address (corporate NAT, CGNAT) a
 * burst of tabs can spend that budget between them. Treating the resulting 429
 * like a 401 would sign the user out over a limit that expires within the
 * minute, holding a refresh token that is still perfectly valid.
 *
 * Narrow on purpose: only the status, and only where the caller asks. A broad
 * "retryable error" predicate would sooner or later swallow a real 401.
 */
export function isRateLimited(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 429;
}

function isStaleActiveTenantRejection(error: unknown): boolean {
  if (!axios.isAxiosError(error) || error.response?.status !== 403) return false;
  if (!requestCarriedActiveTenantHeader(error.config)) return false;
  const data = error.response.data as ApiErrorResponse | undefined;
  return data?.error_code === 'FORBIDDEN' && data?.message === ACTIVE_TENANT_DENIED_MESSAGE;
}

/**
 * Stale-slug recovery: drop a tenant the backend no longer accepts.
 *
 * The situation this exists for: a user is removed from an organisation (or it
 * is deleted) while `kp_active_tenant_slug` still names it. Every global
 * catalogue request then answers 403 — the catalogue is unusable and no amount
 * of navigating fixes it, because the dead slug is persisted. Clearing it
 * returns the caller to their personal scope, which always resolves.
 *
 * De-duplicated with an in-flight flag: a page typically fires several
 * catalogue requests at once and every one of them fails, but the tenant list
 * must be reloaded once, not once per request.
 */
function recoverFromStaleActiveTenant(error: unknown): void {
  if (!isStaleActiveTenantRejection(error)) return;
  if (_activeTenantRecoveryInFlight) return;
  _activeTenantRecoveryInFlight = true;

  // Drop the dead slug synchronously: requests fired between now and the end of
  // the reload must not carry it again. It also makes the reload itself safe —
  // the tenant-list request goes out header-less and so cannot be refused for
  // the very reason it is trying to repair (no recovery loop by construction).
  setActiveTenantSlug(null);

  const handler = _activeTenantRejectedHandler;
  if (!handler) {
    _activeTenantRecoveryInFlight = false;
    return;
  }
  void Promise.resolve()
    .then(handler)
    .catch(() => undefined)
    .finally(() => {
      _activeTenantRecoveryInFlight = false;
    });
}

/** Rejection path of the global client: attempt recovery, then map the envelope. */
function handleGlobalClientError(error: unknown): never {
  recoverFromStaleActiveTenant(error);
  rethrowApiError(error);
}

const client = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Attach the active tenant to every global request (#1091, ADR-009).
 *
 * Deliberately **not** awaiting {@link waitForTenantSlug}: unlike `tenantClient`,
 * where a missing slug produces a structurally wrong URL that can only 404, a
 * missing slug here is a *valid* request — the backend reads a header-less
 * request as "no org context" and answers in personal scope. Blocking would
 * therefore trade a correct answer for a delay, and it would apply to every
 * global route including `/auth/login` and `/auth/refresh`, i.e. it would stall
 * the very bootstrap that produces the slug (up to 10s per request, on a request
 * that has nothing to do with tenants).
 *
 * The accepted consequence: a request fired before `loadMyTenants` resolves
 * carries no header and is answered in personal scope. That window is bounded by
 * the bootstrap and only ever *narrows* what a caller sees; the alternative
 * would be a regression for everyone in exchange.
 *
 * Uniform by design — no light-mode branch. In light mode (REQ-027) the seeded
 * operator holds a `lead` membership in the `mein-garten` tenant, so
 * `loadMyTenants` resolves the active slug to `mein-garten` exactly like any
 * other tenant, and this interceptor sends it; before that resolves it sends
 * nothing, which the backend accepts as well. Hard-coding the light-mode slug
 * here (as `tenantClient` must, because it builds a URL) would add a second
 * source of truth for a value the store already supplies.
 *
 * `tenantClient` gets no such interceptor: its routes bind their tenant from the
 * `/t/{slug}/` path, which is authoritative there.
 */
client.interceptors.request.use((config) => {
  const slug = getActiveTenantSlug();
  if (slug) {
    config.headers.set(ACTIVE_TENANT_HEADER, slug);
  }
  return config;
});

client.interceptors.response.use((response) => response, handleGlobalClientError);

/**
 * Axios client for tenant-scoped API endpoints.
 * Automatically prepends /t/{tenant_slug} to all request URLs
 * using the active tenant slug from localStorage.
 */
const tenantClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

tenantClient.interceptors.request.use(async (config) => {
  let slug = isLightMode ? LIGHT_MODE_SLUG : _activeTenantSlug;
  if (!slug && !isLightMode) {
    // Wait out the auth-bootstrap window instead of firing a doomed
    // unprefixed request; after the timeout (genuinely logged out) the
    // request proceeds unprefixed and fails like before.
    slug = await waitForTenantSlug();
  }
  if (slug && config.url && !config.url.startsWith('/t/')) {
    config.url = `/t/${slug}${config.url}`;
  }
  return config;
});

tenantClient.interceptors.response.use((response) => response, rethrowApiError);

export { tenantClient };
export default client;
