/**
 * The PII rules of the browser error tracker (#777, UI-NFR-013 v1.4 CI-006).
 *
 * Its own chunk, loaded together with the SDK only once error reporting is
 * permitted (`errorTracking.ts` `loadAndInit`) — none of it is needed, and none
 * of it is downloaded, before that.
 *
 * Two kinds of rule:
 *
 * - **by name** — values under credential- or personal-looking names are
 *   redacted wherever they appear (`isSensitiveName`);
 * - **by place in a URL** — the path survives as the grouping signal an event
 *   needs, but not what in it identifies a person or a record: the tenant slug
 *   (a personal garden's slug is derived from the person's display name, REQ-024),
 *   record keys and tokens (`maskPath`). Frontend paths are matched against the
 *   parameterised routes of `routes/AppRoutes.tsx`; backend paths have no route
 *   table in the browser, so outside `/t/:tenant`, `tenants` and `invitations`
 *   a key is recognised by its shape (digit, UUID, token length).
 *
 * The *policy* mirrors `src/libs/kp_errortracking/` on the Python side (allow
 * the route, never the payload); the code is restated because the event shapes
 * differ.
 */

/**
 * Substrings that mark a value as a credential or personal datum wherever it
 * appears *by name*. Matched case-insensitively against the name only, so no
 * secret has to be recognised by its shape.
 *
 * Coordinates are personal data too: a site's `gps_coordinates` is the home
 * address of a personal garden, and the field map's own position (REQ-053
 * GP-UX-026) must never leave the device (SR-019).
 */
const SENSITIVE_NAME_PARTS = [
  'authorization',
  'api_key',
  'apikey',
  'cookie',
  'coords',
  'credential',
  'email',
  'geolocation',
  'gps',
  'latitude',
  'longitude',
  'passwd',
  'password',
  'secret',
  'session',
  'token',
];

const REDACTED = '[redacted]';

/**
 * The parameterised frontend routes (`routes/AppRoutes.tsx`), most specific
 * first. The guard `test/guards/trackerMasksRouteParams.test.ts` fails when a
 * route with a parameter is missing here.
 */
export const FRONTEND_PARAM_ROUTES: readonly string[] = [
  'email-change/revert/:token',
  'email-change/:token',
  'verify-email/:token',
  'password-reset/:token',
  'admin/tenants/:key',
  'admin/users/:key',
  'stammdaten/botanical-families/:key',
  'stammdaten/species/:speciesKey/cultivars/:cultivarKey',
  'stammdaten/species/:key',
  'stammdaten/activities/:key',
  'standorte/sites/:key/plan',
  'standorte/sites/:key/rotation-matrix',
  'standorte/sites/:key',
  'standorte/locations/:key',
  'standorte/substrates/batches/:key',
  'standorte/substrates/:key',
  'standorte/slots/:key',
  'standorte/tanks/:key',
  'pflanzen/plant-instances/:key',
  'duengung/fertilizers/:key',
  'duengung/plans/:key',
  'duengung/feeding-events/:key',
  'giessprotokoll/:key',
  'pflanzenschutz/pests/:key',
  'pflanzenschutz/treatments/:key',
  'ernte/batches/:key',
  'aufgaben/tasks/:key',
  'aufgaben/workflows/:key',
  'aufgaben/activity-plans/:speciesKey',
  'phasen/definitionen/:key',
  'phasen/ablaeufe/:key',
  'durchlaeufe/planting-runs/:key',
  'durchlaeufe/succession-plans/:key',
];

const ROUTE_SEGMENTS = FRONTEND_PARAM_ROUTES.map((route) => route.split('/'));

/** Backend segments after which the next segment names a tenant or a token. */
const NEXT_SEGMENT_PARAM: Record<string, string> = {
  t: ':tenant',
  tenants: ':tenant',
  invitations: ':token',
};

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const API_VERSION = /^v\d+$/;
const WORDS = /^[a-z]+(?:[-_][a-z]+)*$/;

/** Whether a path segment looks like a record key or a token rather than a word of the route. */
function looksLikeKey(segment: string): boolean {
  if (API_VERSION.test(segment)) return false;
  return /\d/.test(segment) || UUID.test(segment) || (segment.length >= 24 && !WORDS.test(segment));
}

function maskFrontendRoute(segments: string[]): string[] | null {
  for (const route of ROUTE_SEGMENTS) {
    if (segments.length !== route.length) continue;
    if (route.every((part, i) => part.startsWith(':') || part === segments[i])) {
      return route.map((part, i) => (part.startsWith(':') ? part : segments[i]!));
    }
  }
  return null;
}

/**
 * Mask what identifies a tenant, a record or a token in a URL path, keeping its
 * shape: `/api/v1/t/max-mustermann/plant-instances/12345` becomes
 * `/api/v1/t/:tenant/plant-instances/:id`, `/password-reset/<token>` becomes
 * `/password-reset/:token`.
 */
export function maskPath(path: string): string {
  const leading = path.startsWith('/') ? '/' : '';
  const trailing = path.length > 1 && path.endsWith('/') ? '/' : '';
  const inner = path.slice(leading.length, path.length - trailing.length);
  if (!inner) return path;
  const parts = inner.split('/');
  const masked =
    (parts[0] === 'api' ? null : maskFrontendRoute(parts)) ??
    parts.map((segment, i) => {
      const previous = i > 0 ? parts[i - 1]! : undefined;
      if (
        previous !== undefined &&
        segment !== '' &&
        Object.prototype.hasOwnProperty.call(NEXT_SEGMENT_PARAM, previous)
      ) {
        return NEXT_SEGMENT_PARAM[previous]!;
      }
      return segment !== '' && looksLikeKey(segment) ? ':id' : segment;
    });
  return leading + masked.join('/') + trailing;
}

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
 * Query and fragment parameters whose values may stay (UI-NFR-013 v1.6 CI-006 b):
 * the ones the app actually uses for paging, sorting and view state, and only
 * with a number-like or enum-like value. Every other value — the table search
 * `q`, a bed name, a redirect target, an e-mail — becomes `[redacted]`; the name
 * stays, it is the useful part for triage.
 */
const NUMERIC_PARAMS = new Set(['page', 'pageSize', 'offset', 'limit', 'year', 'years']);
const ENUM_PARAMS = new Set(['sort', 'dir', 'mode', 'tab', 'format', 'status', 'scope']);
const NUMERIC_VALUE = /^\d{1,6}(?:,\d{1,6})*$/;
const ENUM_VALUE = /^[A-Za-z0-9_.-]{1,32}$/;

function keepsValue(name: string, value: string): boolean {
  if (NUMERIC_PARAMS.has(name)) return NUMERIC_VALUE.test(value);
  if (ENUM_PARAMS.has(name)) return ENUM_VALUE.test(value);
  return false;
}

/** Redact every parameter value of a query string or fragment except the positive list. */
function scrubParams(params: string): string {
  return params
    .split('&')
    .map((pair) => {
      const eq = pair.indexOf('=');
      if (eq < 0) return pair;
      const name = pair.slice(0, eq);
      const value = pair.slice(eq + 1);
      if (value === '') return pair;
      return keepsValue(name, value) ? pair : `${name}=${REDACTED}`;
    })
    .join('&');
}

const ORIGIN = /^[a-z][a-z0-9+.-]*:\/\/[^/?#]*/i;

/**
 * Mask the path (`maskPath`), drop credentials from the origin and redact the
 * values of query string and fragment (`scrubParams`). Origin host and route
 * shape survive — they are the grouping signal.
 */
export function scrubUrl(url: string): string {
  const hashAt = url.indexOf('#');
  const beforeHash = hashAt < 0 ? url : url.slice(0, hashAt);
  const fragment = hashAt < 0 ? null : url.slice(hashAt + 1);
  const queryAt = beforeHash.indexOf('?');
  const base = queryAt < 0 ? beforeHash : beforeHash.slice(0, queryAt);
  const query = queryAt < 0 ? null : beforeHash.slice(queryAt + 1);
  const rawOrigin = ORIGIN.exec(base)?.[0] ?? '';
  // `https://user:secret@host` — the user info is a credential, not a location.
  const origin = rawOrigin.replace(/\/\/[^/@]*@/, '//');
  const path = base.slice(rawOrigin.length);
  let scrubbed = origin + (path ? maskPath(path) : '');
  if (query !== null) scrubbed += query ? `?${scrubParams(query)}` : '?';
  if (fragment !== null) scrubbed += `#${scrubParams(fragment)}`;
  return scrubbed;
}

/**
 * URLs and paths inside free text: an Axios message, a console line, React
 * Router's `No routes matched location "/standorte/sites/…"`. Absolute URLs,
 * `/api/vN/…` anywhere, and other paths when they start a quoted string, follow
 * a space or open the text.
 */
const URL_IN_TEXT = /(?:[a-z][a-z0-9+.-]*:\/\/[^\s"'<>()]+|\/api\/v\d+\/[^\s"'<>()]+)/gi;
const PATH_IN_TEXT = /(^|[\s"'(=])(\/[A-Za-z0-9][^\s"'<>()]*)/g;

/** Apply {@link scrubUrl} to every URL or path inside a text. */
export function maskUrlsInText(text: string): string {
  return text
    .replace(URL_IN_TEXT, (match) => scrubUrl(match))
    .replace(PATH_IN_TEXT, (_match, before: string, path: string) => before + scrubUrl(path));
}

const MAX_DEPTH = 5;

/** Mask URLs in every string of a record, also in nested objects and arrays (depth ≤ 5). */
function maskStringsIn(value: unknown, depth = 0): unknown {
  if (typeof value === 'string') return maskUrlsInText(value);
  if (depth >= MAX_DEPTH || value === null || typeof value !== 'object') return value;
  if (Array.isArray(value)) {
    for (let i = 0; i < value.length; i += 1) value[i] = maskStringsIn(value[i], depth + 1);
    return value;
  }
  const record = value as Record<string, unknown>;
  for (const key of Object.keys(record)) {
    record[key] = isSensitiveName(key) ? REDACTED : maskStringsIn(record[key], depth + 1);
  }
  return record;
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
    // The Referer is the previous page's full URL.
    if (headers) maskStringsIn(headers);
  }

  if (typeof event.transaction === 'string') {
    event.transaction = maskUrlsInText(maskPath(event.transaction));
  }
  if (typeof event.message === 'string') event.message = maskUrlsInText(event.message);

  const exception = event.exception as { values?: Record<string, unknown>[] } | undefined;
  for (const value of exception?.values ?? []) {
    if (typeof value.value === 'string') value.value = maskUrlsInText(value.value);
  }

  const user = event.user as Record<string, unknown> | undefined;
  if (user) {
    // The id is the join key that makes an issue actionable; the attributes
    // that identify the human are not.
    event.user = { id: user.id, tenant: user.tenant };
  }

  for (const section of ['extra', 'tags', 'contexts'] as const) {
    const value = event[section] as Record<string, unknown> | undefined;
    if (value) maskStringsIn(value);
  }

  return event;
}

/** `[aria-label="Tomate Berta"]` → `[aria-label]`: the app puts plant and person names there. */
const LABEL_ATTRIBUTE = /\[(aria-label|title|alt)="(?:[^"\\]|\\.)*"\]/g;

/**
 * `beforeBreadcrumb`: the same rules for the trail leading up to the event.
 *
 * - `ui.input` is dropped wholesale: which fields a user touched is context we
 *   have no reason to ship.
 * - `ui.click`: the SDK describes the target with its `aria-label`, `title` and
 *   `alt` values (`htmlTreeAsString`, no masking option is passed by the
 *   breadcrumbs integration in 11.16) — their values are removed here.
 * - `console`: the SDK keeps the raw arguments in `data.arguments` next to the
 *   formatted `message`; the arguments are dropped, the message is masked.
 */
export function scrubBreadcrumb(crumb: Record<string, unknown>): Record<string, unknown> | null {
  if (crumb.category === 'ui.input') return null;

  if (typeof crumb.message === 'string') {
    let message = crumb.message;
    if (crumb.category === 'ui.click') message = message.replace(LABEL_ATTRIBUTE, '[$1]');
    crumb.message = maskUrlsInText(message);
  }
  const data = crumb.data as Record<string, unknown> | undefined;
  if (data) {
    if (crumb.category === 'console') delete data.arguments;
    if (typeof data.url === 'string') data.url = scrubUrl(data.url);
    if (typeof data.from === 'string') data.from = scrubUrl(data.from);
    if (typeof data.to === 'string') data.to = scrubUrl(data.to);
    maskStringsIn(data);
  }
  return crumb;
}
