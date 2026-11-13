/**
 * The caption of a plan (REQ-053 GP-UX-071, #2913): a `text_label` garden object. Its text is the object's `label`,
 * its box a rect geometry - origin = the anchor (lower left of the text), `length_m` = the text height, `width_m` =
 * the text run, `rotation_deg` = its turn. The server holds the same rules (`garden_object.py`); the editor checks
 * them before the save so a refusal never reaches the user as a 422.
 */
import type { GardenObject, Geometry, Point } from './types';

/** The longest caption (the server's `TEXT_LABEL_MAX_CHARS`). */
export const TEXT_LABEL_MAX_CHARS = 80;
/** The glyphs fill this share of the box's height (the server's `TEXT_LABEL_HEIGHT_SHARE`). */
export const TEXT_LABEL_HEIGHT_SHARE = 0.8;
/** Average glyph width as a share of the font size (the server's `TEXT_LABEL_GLYPH_EM`). */
export const TEXT_LABEL_GLYPH_EM = 0.6;
/** A new caption is this many screen pixels high at the zoom it is set at - readable where it was written. */
export const NEW_TEXT_LABEL_PX = 20;
/** Bounds of a new caption's height in metres: never below the plan's 1 cm, never a wall of text. */
const MIN_TEXT_HEIGHT_M = 0.05;
const MAX_TEXT_HEIGHT_M = 2;

/** Bidi embeddings, overrides, isolates and marks: they could show another text than the one stored. */
const BIDI_CONTROLS = /[\u202a-\u202e\u2066-\u2069\u200e\u200f\u061c]/u;
/** Line breaks of any kind and the other control characters (Unicode `Cc`, `Zl`, `Zp`). */
const CONTROLS = /[\p{Cc}\u2028\u2029]/u;

export type TextLabelProblem = 'empty' | 'too_long' | 'control';

/** The length in characters as the server counts them (code points, not UTF-16 units). */
export function textLength(text: string): number {
  return Array.from(text).length;
}

/** Why `text` is no caption (after trimming), or `null`: empty, too long, a line break or another control. */
export function textLabelProblem(text: string): TextLabelProblem | null {
  const trimmed = text.trim();
  if (trimmed === '') return 'empty';
  if (textLength(trimmed) > TEXT_LABEL_MAX_CHARS) return 'too_long';
  if (CONTROLS.test(trimmed) || BIDI_CONTROLS.test(trimmed)) return 'control';
  return null;
}

export function isTextLabel(object: Pick<GardenObject, 'object_type'> | null | undefined): boolean {
  return object?.object_type === 'text_label';
}

/** The font size of a caption in metres: its box's height share, smaller where the text would run past the width. */
export function textLabelFontM(widthM: number, lengthM: number, text: string): number {
  const byHeight = lengthM * TEXT_LABEL_HEIGHT_SHARE;
  return Math.min(byHeight, widthM / (Math.max(1, textLength(text)) * TEXT_LABEL_GLYPH_EM));
}

/** Rounded up to the plan's storage precision (1 mm), so a box never comes out a hair too small for its text. */
function ceilMm(value: number): number {
  return Math.ceil(value * 1000 - 1e-9) / 1000;
}

/** The text height of a new caption set at `pxPerM`: {@link NEW_TEXT_LABEL_PX} on screen, within the bounds. */
export function newTextHeightM(pxPerM: number): number {
  const raw = NEW_TEXT_LABEL_PX / Math.max(pxPerM, 1e-6);
  return ceilMm(Math.min(MAX_TEXT_HEIGHT_M, Math.max(MIN_TEXT_HEIGHT_M, raw)));
}

/** The box `text` takes at the height `lengthM`: as wide as its glyphs at the full font size. */
export function textBoxWidthM(text: string, lengthM: number): number {
  const font = lengthM * TEXT_LABEL_HEIGHT_SHARE;
  return ceilMm(Math.max(lengthM, textLength(text.trim()) * font * TEXT_LABEL_GLYPH_EM));
}

/** The rect of a new caption at `anchor` (its lower-left corner), unturned. */
export function textLabelGeometry(anchor: Point, text: string, lengthM: number): Geometry {
  return {
    kind: 'rect',
    origin: [anchor[0], anchor[1]],
    width_m: textBoxWidthM(text, lengthM),
    length_m: lengthM,
    rotation_deg: 0,
  };
}

/**
 * The box after the text of a caption changed: the same height, anchor and turn, the width that fits the new text -
 * so a longer text stays as large as it was instead of shrinking into the old box. `null` when it is no rect.
 */
export function refitTextLabel(geometry: Geometry, text: string): Geometry | null {
  if (geometry.kind !== 'rect') return null;
  const width = textBoxWidthM(text, geometry.length_m);
  return width === geometry.width_m ? geometry : { ...geometry, width_m: width };
}
