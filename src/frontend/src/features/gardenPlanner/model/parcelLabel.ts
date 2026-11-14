/**
 * The parcel label of a location (REQ-053 GP-FR-176, #2759): an optional, stable identifier such as an allotment
 * parcel number. The server holds the same rules (`app/domain/models/parcel_label.py`): one line, at most
 * {@link PARCEL_LABEL_MAX_CHARS} characters, no control or bidi format character; surrounding space is stripped and
 * a blank text is no label. The editor checks them before the save so a refusal never reaches the user as a 422.
 */
import { textLabelProblem, textLength } from './textLabel';

/** The longest parcel label (the server's `PARCEL_LABEL_MAX_CHARS`). */
export const PARCEL_LABEL_MAX_CHARS = 40;

export type ParcelLabelProblem = 'too_long' | 'control';

/** Why `text` is no parcel label (after trimming), or `null`. A blank text is fine: it clears the label. */
export function parcelLabelProblem(text: string): ParcelLabelProblem | null {
  const trimmed = text.trim();
  if (trimmed === '') return null;
  if (textLength(trimmed) > PARCEL_LABEL_MAX_CHARS) return 'too_long';
  // The caption's rule for line breaks, controls and bidi characters; its length limit is the longer one.
  return textLabelProblem(trimmed) === 'control' ? 'control' : null;
}

/** The value to store for `text`: trimmed, `null` when blank. */
export function parcelLabelValue(text: string): string | null {
  const trimmed = text.trim();
  return trimmed === '' ? null : trimmed;
}
