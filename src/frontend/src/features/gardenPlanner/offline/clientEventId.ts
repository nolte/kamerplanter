/**
 * The `client_event_id` of a write that must never land twice (REQ-053 WP 9.3, G-W9 f).
 *
 * A module of its own so an online write (the "rain - skipped" action of the watering-round dialog, WP 9.13) can
 * make one without pulling the offline write queue and its IndexedDB layer into its chunk.
 */

/** A UUID v4 for `client_event_id`; `crypto.randomUUID` is missing outside a secure context. */
export function newClientEventId(): string {
  const cryptoApi = globalThis.crypto;
  if (typeof cryptoApi?.randomUUID === 'function') return cryptoApi.randomUUID();
  const bytes = new Uint8Array(16);
  cryptoApi.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}
