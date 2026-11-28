/**
 * Optional Sentry-protocol error tracking for the browser bundle (#777).
 *
 * Governing contract: `spec/project/error-tracking/` in `nolte/claude-shared`.
 * GlitchTip is the reference profile; nothing here binds to it.
 *
 * Two properties are load-bearing:
 *
 * 1. **Optional.** The DSN arrives through `runtime-config.js` at container
 *    start, never baked into the build, so one image serves every stage. With
 *    no DSN nothing is initialised.
 * 2. **Near-zero cost when off.** `@sentry/react` is behind a dynamic
 *    `import()`, so it lands in its own chunk that the browser never fetches
 *    unless a DSN is configured and the user consented. Measured against the
 *    UI-NFR-003 initial-payload budget: the SDK chunk is 184 KB gzip and stays
 *    out of it entirely; only this module's own wiring is in the initial
 *    payload, at +1.5 KB gzip (345.5 -> 347.0 KB, budget 400). That is why
 *    `init` is async and awaited before the app mounts rather than imported at
 *    the top.
 * 3. **Consent-gated** (UI-NFR-013 CI-001/CI-002/CW-003, #2159, #3025). A DSN is
 *    the operator's opt-in; the consent `browser_error_reports` is the second,
 *    independent gate, decided by `browserReportsPermitted` over the device
 *    decision, the sign-in state and the account consent (UI-NFR-013 §5.4). The
 *    SDK chunk is neither fetched nor initialised until that says yes — unknown
 *    and undecided count as no, and so does "the auth bootstrap has not finished
 *    yet", so nothing is sent before it is known who is signed in. A decision made
 *    after boot takes effect without a reload: a later grant initialises, a
 *    revoke disables the client synchronously and then closes it. Light mode
 *    (REQ-027) never tracks in the browser, whatever is stored.
 *
 * The PII rules mirror `src/libs/kp_errortracking/` on the Python side. They are
 * restated rather than shared because the two run on different platforms with
 * different event shapes; the *policy* below (allow the route, never the
 * payload) is the part that must agree.
 */

import { runtimeConfig } from '@/config/runtimeConfig';
import { isLightMode } from '@/config/mode';
import {
  browserReportsPermitted,
  readConsentSnapshot,
  subscribeConsent,
} from '@/observability/consent';

type SentryModule = typeof import('@sentry/react');
type ScrubModule = typeof import('@/observability/errorTrackingScrub');

/** What a start loads: the SDK and the PII rules, both behind the consent (CI-002, CI-006). */
interface Loaded {
  sdk: SentryModule;
  scrub: ScrubModule;
}

/**
 * The SDK's `dataCollection` contract, derived from `init`'s own parameter
 * type so it tracks whichever SDK version is installed. (`@sentry/core`
 * exports the `DataCollection` name only from 11 on; the derivation compiles
 * on 10.x and 11 alike.)
 */
type DataCollection = NonNullable<
  NonNullable<Parameters<SentryModule['init']>[0]>['dataCollection']
>;

/**
 * Every category the SDK can collect, minus the three that are deliberately
 * not decided here. `Required` is the point: the resolver takes the SDK's
 * *permissive* default for any category the block does not name, so a minor
 * SDK bump that adds a category must fail the typecheck rather than start
 * collecting it in production.
 *
 * - `frameContextLines`: source code around a frame, not personal data. Not
 *   pinned, so it follows the SDK default — 7 under the old `sendDefaultPii`
 *   bridge, 5 once `dataCollection` is set (the resolver switches its base).
 * - `queryParams`: the deprecated 10.x alias of `urlQueryParams`; gone in 11.
 * - `queues`: 11-only, server-side messaging instrumentation with no browser
 *   reader, and absent from the 10.x typings this must still compile against.
 */
type DecidedDataCollection = Required<
  Omit<DataCollection, 'frameContextLines' | 'queryParams' | 'queues'>
>;

/**
 * The closed stage vocabulary. Identical to `ENVIRONMENTS` in
 * `src/libs/kp_errortracking/kp_errortracking/error_tracking.py` — alert rules
 * filter on these exact strings across backend, worker and browser.
 */
export const ENVIRONMENTS = ['development', 'e2e', 'staging', 'production'] as const;

/** Module-scoped handle, set only after a successful init. */
let sentry: SentryModule | null = null;

/**
 * Upper bound for the post-revoke `close()`. The client is already disabled
 * when it runs, so this only bounds how long the SDK may wait for requests that
 * were in flight before the revoke; it gates nothing.
 */
const CLOSE_TIMEOUT_MS = 2000;

/**
 * The chunk load, shared by every start. One `import()` per page: a grant ->
 * revoke -> grant burst reuses it instead of racing two loads of the same chunk.
 */
let sdkLoad: Promise<Loaded> | null = null;

/** The init in flight, so a burst of consent events loads the SDK once. */
let starting: Promise<boolean> | null = null;

/**
 * Bumped by every stop. An init that was in flight when the user revoked
 * compares its captured value on return and discards itself, so a slow chunk
 * download can never resurrect tracking after a "no".
 */
let generation = 0;

/** The consent subscription, registered once per page by `initErrorTracking`. */
let unsubscribeConsent: (() => void) | null = null;

/** Default integrations that send outside `beforeSend` (UI-NFR-013 §5.3 CI-005). */
export const SENDING_INTEGRATIONS: readonly string[] = ['BrowserSession'];

/** The SDK's integrations minus those that send on their own. */
export function withoutSenders<T extends { name: string }>(defaults: T[]): T[] {
  return defaults.filter((integration) => !SENDING_INTEGRATIONS.includes(integration.name));
}

function resolveSampleRate(raw: string | undefined): number {
  if (raw === undefined || raw === '') return 1;
  const rate = Number(raw);
  if (!Number.isFinite(rate) || rate < 0 || rate > 1) {
    // Sampling is a decision, not an accident — but a malformed one must not
    // silently drop events. Fall back to the documented default and say so.
    console.warn(`[error-tracking] SENTRY_SAMPLE_RATE="${raw}" is invalid, using 1`);
    return 1;
  }
  return rate;
}

function configuredDsn(): string {
  return (runtimeConfig().SENTRY_DSN ?? '').trim();
}

/**
 * Whether the operator configured a DSN. The consent banner only asks for a
 * `browser_error_reports` decision when there is something for it to switch on.
 */
export function isErrorTrackingConfigured(): boolean {
  return configuredDsn() !== '';
}

/**
 * Whether this deployment asks for and reconciles the `browser_error_reports`
 * consent at all: a DSN is configured and it is not Light mode (UI-NFR-013 §5.3).
 */
export function isBrowserConsentManaged(): boolean {
  return !isLightMode && isErrorTrackingConfigured();
}

/** The host error reports go to, for the consent text (CK-004); `null` when the DSN does not parse. */
export function errorTrackerHost(): string | null {
  try {
    return new URL(configuredDsn()).host || null;
  } catch {
    return null;
  }
}

/**
 * Wire error tracking to the DSN and the user's consent.
 *
 * With no DSN nothing happens — no subscription, no chunk, no init. With one,
 * the module subscribes to consent changes (once) and starts the SDK only if the
 * consent decision (`trackingPermitted`) already says yes.
 *
 * @returns `true` when tracking is active, `false` when it stayed off. Callers
 *   ignore this; it exists so the behaviour is directly testable.
 */
export async function initErrorTracking(): Promise<boolean> {
  if (!isErrorTrackingConfigured()) return false;
  if (!unsubscribeConsent) {
    unsubscribeConsent = subscribeConsent(() => {
      void applyConsent();
    });
  }
  return applyConsent();
}

/**
 * Whether the browser may track right now: the consent decision of UI-NFR-013
 * §5.4, evaluated at this moment (an account grant ages out after 30 minutes
 * without a re-read), and never in Light mode — there is no banner there
 * (household exemption), so a grant left over from before a full -> light
 * switch must not start the SDK.
 */
function trackingPermitted(): boolean {
  return !isLightMode && browserReportsPermitted(readConsentSnapshot(), Date.now());
}

/** Start or stop the SDK to match the current consent. */
function applyConsent(): Promise<boolean> {
  if (trackingPermitted()) return startErrorTracking();
  stopErrorTracking();
  return Promise.resolve(false);
}

/**
 * Stop reporting at once (CW-003) and tear the SDK down. Safe when tracking is off.
 *
 * `Sentry.close(timeout)` alone is not immediate: in @sentry/core 11 it awaits
 * `flush(timeout)` and only then sets `enabled = false`, and a timeout of `0`
 * means *unbounded* (`while (!timeout || ticked < timeout)`), so the still-
 * installed global handlers could send for as long as the flush ran. The
 * client is therefore disabled synchronously first; the consent check inside
 * `beforeSend`/`beforeBreadcrumb` covers anything already past that point.
 * `addBreadcrumb` only checks that a client *exists* and writes to the
 * isolation scope, so the revoked session's trail is cleared too — a later
 * re-grant must not ship it.
 */
export function stopErrorTracking(): void {
  generation += 1;
  starting = null;
  const active = sentry;
  sentry = null;
  if (!active) return;
  try {
    const client = active.getClient();
    if (client) client.getOptions().enabled = false;
    active.getIsolationScope().clearBreadcrumbs();
    // `Scope#clear()` no longer exists in SDK 11; breadcrumbs are the only
    // trail this module lets the SDK keep (the user block is scrubbed).
    active.getCurrentScope().clearBreadcrumbs();
  } catch (error) {
    // The tracker cannot report its own shutdown; the console is the only place left to say so.
    console.warn('[error-tracking] disabling the client failed', error);
  }
  active.close(CLOSE_TIMEOUT_MS).catch((error: unknown) => {
    // Same as above: closing is best effort and must never throw into consent handling.
    console.warn('[error-tracking] closing the client failed', error);
  });
}

function loadSdk(): Promise<Loaded> {
  if (!sdkLoad) {
    sdkLoad = Promise.all([
      import('@sentry/react'),
      import('@/observability/errorTrackingScrub'),
    ]).then(([sdk, scrub]) => ({ sdk, scrub }));
    sdkLoad = sdkLoad.catch((error: unknown) => {
      // A failed chunk load may be transient; let the next grant retry it.
      sdkLoad = null;
      throw error;
    });
  }
  return sdkLoad;
}

function startErrorTracking(): Promise<boolean> {
  if (sentry) return Promise.resolve(true);
  if (!starting) {
    const started = loadAndInit(generation).finally(() => {
      if (starting === started) starting = null;
    });
    starting = started;
  }
  return starting;
}

async function loadAndInit(startedIn: number): Promise<boolean> {
  const config = runtimeConfig();
  const dsn = configuredDsn();
  if (!dsn) return false;

  const environment = (config.SENTRY_ENVIRONMENT ?? 'development').trim() || 'development';
  if (!(ENVIRONMENTS as readonly string[]).includes(environment)) {
    // Deliberately not fatal and deliberately not corrected: a stage that
    // refused to report would look exactly like a healthy quiet frontend,
    // whereas a stray value shows up in the tracker's environment list where
    // an operator sees it.
    console.warn(
      `[error-tracking] SENTRY_ENVIRONMENT="${environment}" is outside the declared ` +
        `vocabulary (${ENVIRONMENTS.join(', ')}); alert rules filtering on those will not match.`,
    );
  }

  try {
    const { sdk: Sentry, scrub } = await loadSdk();
    // The user revoked (or the module was reset) while the chunk was loading.
    if (startedIn !== generation || !trackingPermitted()) return false;
    Sentry.init({
      dsn,
      environment,
      // A deployment that configures a DSN configures a release in the same
      // heredoc, so this fallback only ever surfaces in a hand-run container.
      // It is deliberately not silent: an unattributable release makes
      // regression detection impossible, and `@dev` says so in the tracker.
      release: config.SENTRY_RELEASE || 'kamerplanter-frontend@dev',
      // Explicit because the SDK's own defaults are permissive: Sentry 11
      // removed `sendDefaultPii` and, with `dataCollection` left unset, now
      // collects user info (IP), cookies, headers, bodies and query data by
      // default (MIGRATION.md, "`sendDefaultPii` is replaced by
      // `dataCollection`"). Every category is switched off by name, which is
      // stricter than the old `sendDefaultPii: false` bridge (that kept
      // deny-listed headers/cookies/query params and stack-frame variables).
      // Option names are the SDK's own (`DataCollection` in
      // `@sentry/core/build/types/types/datacollection.d.ts`); the
      // `satisfies` closes the set — see `DecidedDataCollection`.
      dataCollection: {
        userInfo: false,
        cookies: false,
        httpHeaders: { request: false, response: false },
        httpBodies: [],
        urlQueryParams: false,
        graphQL: { document: false, variables: false },
        genAI: { inputs: false, outputs: false },
        // `mcp` arrived with @sentry/core 9.16: tool-call inputs and outputs of
        // MCP servers. Off like every other payload category.
        mcp: { inputs: false, outputs: false },
        databaseQueryData: false,
        stackFrameVariables: false,
      } satisfies DecidedDataCollection,
      sampleRate: resolveSampleRate(config.SENTRY_SAMPLE_RATE),
      // UI-NFR-013 CI-005 (#3025): only error events, and only through `beforeSend`.
      // `BrowserSession` starts and sends a session after every init (whenIdleOrHidden),
      // and client reports go out on every tab hide — neither passes `beforeSend`, so
      // neither the consent re-check nor the 30-minute age limit would reach them.
      // Measured in @sentry/browser 11.16.0 (`sdk.js` getDefaultIntegrations, `client.js`).
      integrations: withoutSenders,
      sendClientReports: false,
      // Performance tracing stays advisory per the observability spec and is
      // off until someone decides to adopt it.
      tracesSampleRate: 0,
      // Both hooks re-check consent first: the SDK's global handlers stay
      // installed after a revoke, and these run for whatever they still hand
      // over. `null` drops the event / breadcrumb.
      beforeSend: (event) =>
        (trackingPermitted()
          ? scrub.scrubEvent(event as unknown as Record<string, unknown>)
          : null) as never,
      beforeBreadcrumb: (crumb) =>
        (trackingPermitted()
          ? scrub.scrubBreadcrumb(crumb as unknown as Record<string, unknown>)
          : null) as never,
    });
    sentry = Sentry;
    return true;
  } catch (error) {
    // A tracker that cannot load must never keep the app from starting — that
    // would make an optional feature a availability risk.
    console.warn('[error-tracking] initialisation failed, continuing without it', error);
    return false;
  }
}

/**
 * Report an error that was caught and handled.
 *
 * The SDK's global handlers cover what nobody caught. This is the complement:
 * a React error boundary, or any `catch` that degrades instead of rethrowing,
 * makes the failure invisible to them. A swallowed error is invisible to every
 * phase of the error-tracking contract.
 *
 * No-op when tracking is off, so call sites need no guard.
 */
export function captureHandledError(error: unknown, context?: Record<string, unknown>): void {
  if (!sentry) return;
  sentry.captureException(error, context ? { extra: context } : undefined);
}

/** Whether the SDK is loaded and reporting. Exposed for tests and diagnostics. */
export function isErrorTrackingActive(): boolean {
  return sentry !== null;
}

/** Test seam: drop the loaded SDK handle and the consent subscription. */
export function resetErrorTrackingForTests(): void {
  unsubscribeConsent?.();
  unsubscribeConsent = null;
  generation += 1;
  starting = null;
  sentry = null;
}
