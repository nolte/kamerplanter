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
 *    unless a DSN is configured. Measured against the UI-NFR-003 initial-payload
 *    budget: the SDK chunk is 184 KB gzip and stays out of it entirely; only
 *    this module's own wiring is in the initial payload, at +1.5 KB gzip
 *    (345.5 -> 347.0 KB, budget 400). That is why `init` is async and awaited
 *    before the app mounts rather than imported at the top.
 *
 * The PII rules mirror `src/libs/kp_errortracking/` on the Python side. They are
 * restated rather than shared because the two run on different platforms with
 * different event shapes; the *policy* below (allow the route, never the
 * payload) is the part that must agree.
 */

import { runtimeConfig } from '@/config/runtimeConfig';

type SentryModule = typeof import('@sentry/react');

/**
 * The closed stage vocabulary. Identical to `ENVIRONMENTS` in
 * `src/libs/kp_errortracking/kp_errortracking/error_tracking.py` — alert rules
 * filter on these exact strings across backend, worker and browser.
 */
export const ENVIRONMENTS = ['development', 'e2e', 'staging', 'production'] as const;

/**
 * Substrings that mark a value as a credential or personal datum wherever it
 * appears *by name*. Matched case-insensitively against the name only, so no
 * secret has to be recognised by its shape.
 */
const SENSITIVE_NAME_PARTS = [
  'authorization',
  'api_key',
  'apikey',
  'cookie',
  'credential',
  'email',
  'passwd',
  'password',
  'secret',
  'session',
  'token',
];

const REDACTED = '[redacted]';

/** Module-scoped handle, set only after a successful init. */
let sentry: SentryModule | null = null;

export function isSensitiveName(name: string): boolean {
  const lowered = name.toLowerCase();
  return SENSITIVE_NAME_PARTS.some((part) => lowered.includes(part));
}

/** Redact values under sensitive keys in place, keeping the keys visible. */
export function redactRecord(record: Record<string, unknown>): void {
  for (const key of Object.keys(record)) {
    if (isSensitiveName(key)) {
      record[key] = REDACTED;
    }
  }
}

/**
 * Strip the query string's sensitive parameters while keeping the path.
 *
 * The path is the single most valuable grouping signal an event carries, so it
 * survives; a `?token=…` on it does not. Anything unparseable is returned
 * untouched rather than guessed at.
 */
export function scrubUrl(url: string): string {
  const [base, query] = url.split('?');
  if (!query) return url;
  const scrubbed = query
    .split('&')
    .map((pair) => {
      const eq = pair.indexOf('=');
      if (eq < 0) return pair;
      const name = pair.slice(0, eq);
      return isSensitiveName(name) ? `${name}=${REDACTED}` : pair;
    })
    .join('&');
  return `${base}?${scrubbed}`;
}

/** `beforeSend`: strip personal data before the event leaves the browser. */
export function scrubEvent(event: Record<string, unknown>): Record<string, unknown> {
  const request = event.request as Record<string, unknown> | undefined;
  if (request) {
    // A request body is the richest source of personal data this app has
    // (plant notes, harvest records, invitations); no triage need justifies it.
    delete request.data;
    delete request.cookies;
    if (typeof request.url === 'string') request.url = scrubUrl(request.url);
    if (typeof request.query_string === 'string') {
      request.query_string = scrubUrl(`?${request.query_string}`).slice(1);
    }
    const headers = request.headers as Record<string, unknown> | undefined;
    if (headers) redactRecord(headers);
  }

  const user = event.user as Record<string, unknown> | undefined;
  if (user) {
    // The id is the join key that makes an issue actionable; the attributes
    // that identify the human are not.
    event.user = { id: user.id, tenant: user.tenant };
  }

  for (const section of ['extra', 'tags', 'contexts'] as const) {
    const value = event[section] as Record<string, unknown> | undefined;
    if (value) redactRecord(value);
  }

  return event;
}

/**
 * `beforeBreadcrumb`: the same rules for the trail leading up to the event.
 *
 * `ui.input` breadcrumbs are dropped wholesale. The SDK records only that an
 * input happened, not its value — but the trail of *which* fields a user
 * touched on a member-invitation or health-observation form is itself context
 * we have no reason to ship, and dropping the category is cheaper to reason
 * about than auditing what a future SDK version decides to attach.
 */
export function scrubBreadcrumb(crumb: Record<string, unknown>): Record<string, unknown> | null {
  if (crumb.category === 'ui.input') return null;

  const data = crumb.data as Record<string, unknown> | undefined;
  if (data) {
    if (typeof data.url === 'string') data.url = scrubUrl(data.url);
    if (typeof data.from === 'string') data.from = scrubUrl(data.from);
    if (typeof data.to === 'string') data.to = scrubUrl(data.to);
    redactRecord(data);
  }
  return crumb;
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

/**
 * Load and initialise the SDK when a DSN is configured.
 *
 * @returns `true` when tracking is active, `false` when it stayed off. Callers
 *   ignore this; it exists so the behaviour is directly testable.
 */
export async function initErrorTracking(): Promise<boolean> {
  const config = runtimeConfig();
  const dsn = (config.SENTRY_DSN ?? '').trim();
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
    const Sentry = await import('@sentry/react');
    Sentry.init({
      dsn,
      environment,
      // A deployment that configures a DSN configures a release in the same
      // heredoc, so this fallback only ever surfaces in a hand-run container.
      // It is deliberately not silent: an unattributable release makes
      // regression detection impossible, and `@dev` says so in the tracker.
      release: config.SENTRY_RELEASE || 'kamerplanter-frontend@dev',
      sendDefaultPii: false,
      sampleRate: resolveSampleRate(config.SENTRY_SAMPLE_RATE),
      // Performance tracing stays advisory per the observability spec and is
      // off until someone decides to adopt it.
      tracesSampleRate: 0,
      beforeSend: (event) => scrubEvent(event as unknown as Record<string, unknown>) as never,
      beforeBreadcrumb: (crumb) =>
        scrubBreadcrumb(crumb as unknown as Record<string, unknown>) as never,
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

/** Test seam: drop the loaded SDK handle. */
export function resetErrorTrackingForTests(): void {
  sentry = null;
}
