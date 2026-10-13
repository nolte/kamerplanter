/**
 * Send the browser to another origin with a full page load — e.g. an identity
 * provider's authorization URL (#1815).
 *
 * A module of its own so tests can replace it: jsdom's `window.location.assign`
 * cannot be spied on.
 */
export function redirectTo(url: string): void {
  window.location.assign(url);
}
