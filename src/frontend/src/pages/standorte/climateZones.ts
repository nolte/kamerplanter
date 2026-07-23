/**
 * USDA hardiness zones in the half-zone format `\d{1,2}[ab]` (1a–13b) — the
 * structured vocabulary behind the (legacy free-text) site `climate_zone` field
 * (REQ-002/REQ-039). Kept in sync with the backend `_HARDINESS_ZONE_PATTERN`
 * in `site.py`, which the winter-hardiness "Ampel" and the hardiness-zone
 * resolver expect.
 */
export const USDA_HARDINESS_ZONES: readonly string[] = Array.from(
  { length: 13 },
  (_, i) => i + 1,
).flatMap((zone) => [`${zone}a`, `${zone}b`]);
