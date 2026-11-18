/**
 * Open-redirect protection for any URL the app follows or renders as a link but did not write itself (AI tip
 * `action_url`, notification `action_url`, the sign-in `returnTo`).
 *
 * Only a same-origin, root-relative app path survives: the string must start with exactly one `/`, carry no
 * backslash (raw or percent-encoded) and no control character, and still resolve to this origin with a path that is
 * not protocol-relative. Browsers normalise `\` to `/` in special-scheme URLs, so `/\evil.example` is the
 * protocol-relative `//evil.example` to them, and a tab or newline is stripped before parsing (`/\t/evil.example`).
 */
export function toSameOriginAppPath(raw: string | null | undefined): string | null {
  if (typeof raw !== 'string' || !raw.startsWith('/') || raw.startsWith('//')) return null;
  // eslint-disable-next-line no-control-regex -- refusing control characters is the point of this check
  if (/[\u0000-\u001f\u007f\\]|%5c/i.test(raw)) return null;
  let url: URL;
  try {
    url = new URL(raw, window.location.origin);
  } catch {
    return null;
  }
  if (url.origin !== window.location.origin) return null;
  // Dot segments resolve during parsing (`/.//evil.example`, `/%2e%2e//evil.example` -> `//evil.example`): check the
  // path that is returned, not only the raw input, so the result is never protocol-relative.
  if (url.pathname.startsWith('//') || url.pathname.includes('\\')) return null;
  return `${url.pathname}${url.search}${url.hash}`;
}
