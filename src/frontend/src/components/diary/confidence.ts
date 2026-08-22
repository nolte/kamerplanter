/**
 * REQ-051 §6.4 / AK-30 — putting a finding's confidence into words.
 *
 * A bare percentage is explicitly not enough: it suggests a precision a language
 * model does not have. Every place that shows a confidence shows the number
 * *and* one of these bands, so "72 %" always arrives as "72 % — eher
 * wahrscheinlich" rather than as a measurement.
 *
 * The band boundaries are a deliberate, coarse five-step scale. Finer steps
 * would re-introduce exactly the false precision the criterion exists to
 * prevent.
 */

/** Qualitative band of a confidence value; maps to `enums.diaryConfidence.*`. */
export type ConfidenceBand = 'veryLow' | 'low' | 'moderate' | 'high' | 'veryHigh';

/** Colour intent per band, used for the chip/label rendering. */
export type ConfidenceSeverity = 'error' | 'warning' | 'info' | 'success';

/**
 * Classify a 0.0–1.0 confidence into its qualitative band.
 *
 * Values outside the range are clamped rather than rejected: the backend
 * validates `0.0 <= confidence <= 1.0` (§4.5), and a display component is the
 * wrong place to blow up over a value that got past it anyway.
 */
export function confidenceBand(confidence: number): ConfidenceBand {
  const value = Number.isFinite(confidence) ? Math.min(Math.max(confidence, 0), 1) : 0;
  if (value < 0.2) return 'veryLow';
  if (value < 0.4) return 'low';
  if (value < 0.6) return 'moderate';
  if (value < 0.8) return 'high';
  return 'veryHigh';
}

/** Colour intent of a band — low confidence must not read as a green result. */
export function confidenceSeverity(band: ConfidenceBand): ConfidenceSeverity {
  switch (band) {
    case 'veryLow':
    case 'low':
      return 'warning';
    case 'moderate':
      return 'info';
    default:
      return 'success';
  }
}

/**
 * Render a confidence as a whole-number percentage.
 *
 * Rounded to integers on purpose: "71.5 %" would claim half a percentage point
 * of resolution from a model that produced the number by estimation.
 */
export function confidencePercent(confidence: number): number {
  const value = Number.isFinite(confidence) ? Math.min(Math.max(confidence, 0), 1) : 0;
  return Math.round(value * 100);
}
